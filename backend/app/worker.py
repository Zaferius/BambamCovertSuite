import json
import os
import socket
import threading
import time
import uuid

from redis import Redis
from rq import Queue
from rq import Retry
from rq import Worker

from app.core.config import get_settings


WORKER_STATUS_KEY = "worker_status"
WORKER_TARGET_COUNT_KEY = "worker_target_count"
WORKER_SCALE_LOCK_KEY = "worker_scale_lock"


def get_queue() -> Queue:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    return Queue("bambam-jobs", connection=connection)


def get_redis_connection() -> Redis:
    return get_queue().connection


def set_worker_target_count(target_count: int) -> None:
    get_redis_connection().set(WORKER_TARGET_COUNT_KEY, str(target_count))


def get_worker_target_count() -> int:
    settings = get_settings()
    raw = get_redis_connection().get(WORKER_TARGET_COUNT_KEY)
    if raw is None:
        return settings.worker_target_default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return settings.worker_target_default


def list_worker_statuses() -> list[dict]:
    connection = get_redis_connection()
    rows = connection.hgetall(WORKER_STATUS_KEY)
    workers: list[dict] = []
    for worker_id_raw, payload_raw in rows.items():
        try:
            payload = json.loads(payload_raw)
            worker_id = worker_id_raw.decode("utf-8", errors="ignore") if isinstance(worker_id_raw, bytes) else str(worker_id_raw)
            payload.setdefault("worker_id", worker_id)
            workers.append(payload)
        except Exception:
            # best-effort cleanup for malformed data
            try:
                connection.hdel(WORKER_STATUS_KEY, worker_id_raw)
            except Exception:
                pass
    return workers


def set_worker_status(worker_id: str, payload: dict) -> None:
    get_redis_connection().hset(WORKER_STATUS_KEY, worker_id, json.dumps(payload))


def remove_worker_status(worker_id: str) -> None:
    get_redis_connection().hdel(WORKER_STATUS_KEY, worker_id)


def cancel_all_jobs() -> int:
    """Empty the Redis queues."""
    count = 0
    try:
        count += get_queue().empty()
    except Exception:
        pass
    return count


def enqueue_job(func, *args, **kwargs):
    settings = get_settings()
    timeout = kwargs.pop("job_timeout", settings.queue_default_timeout)
    retry_max = kwargs.pop("retry_max", 1)
    job_type = kwargs.pop("job_type", None)
    queue = get_queue()
    meta = kwargs.pop("meta", {}) or {}
    if job_type:
        meta["job_type"] = str(job_type)
    return queue.enqueue(
        func,
        *args,
        job_timeout=timeout,
        failure_ttl=settings.queue_failure_ttl_seconds,
        result_ttl=settings.queue_result_ttl_seconds,
        retry=Retry(max=retry_max, interval=[10, 30]) if retry_max > 0 else None,
        meta=meta,
        **kwargs,
    )


def _now() -> int:
    return int(time.time())


class TrackedWorker(Worker):
    def __init__(self, *args, worker_id: str, heartbeat_interval: int, **kwargs):
        super().__init__(*args, **kwargs)
        self._worker_id = worker_id
        self._heartbeat_interval = heartbeat_interval
        self._shutdown = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._status_lock = threading.Lock()
        # NOTE:
        # rq.Worker already uses an internal `_state` attribute (WorkerStatus enum).
        # Do not shadow it with a dict, otherwise worker lifecycle updates inside RQ
        # will replace the dict and break our item assignment/status serialization.
        self._status_payload = {
            "worker_id": worker_id,
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "status": "idle",
            "current_job_id": None,
            "current_job_type": None,
            "last_seen": _now(),
            "started_at": _now(),
            "last_error": None,
        }

    def _write_status(self) -> None:
        with self._status_lock:
            payload = dict(self._status_payload)
            payload["last_seen"] = _now()
            self._status_payload["last_seen"] = payload["last_seen"]
        set_worker_status(self._worker_id, payload)

    def _heartbeat_loop(self) -> None:
        while not self._shutdown.is_set():
            self._write_status()
            self._shutdown.wait(self._heartbeat_interval)

    def _set_busy(self, job) -> None:
        with self._status_lock:
            self._status_payload["status"] = "busy"
            self._status_payload["current_job_id"] = job.id
            self._status_payload["current_job_type"] = (job.meta or {}).get("job_type")
        self._write_status()

    def _set_idle(self, last_error: str | None = None) -> None:
        with self._status_lock:
            self._status_payload["status"] = "idle"
            self._status_payload["current_job_id"] = None
            self._status_payload["current_job_type"] = None
            self._status_payload["last_error"] = last_error
        self._write_status()

    def execute_job(self, job, queue):
        self._set_busy(job)
        failed_message: str | None = None
        try:
            return super().execute_job(job, queue)
        except Exception as exc:
            failed_message = str(exc)
            raise
        finally:
            self._set_idle(last_error=failed_message)

    def work(self, *args, **kwargs):
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        self._write_status()
        try:
            return super().work(*args, **kwargs)
        finally:
            self._shutdown.set()
            remove_worker_status(self._worker_id)


if __name__ == "__main__":
    settings = get_settings()
    queue = get_queue()
    worker_id = f"{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    worker = TrackedWorker(
        [queue],
        connection=queue.connection,
        worker_id=worker_id,
        heartbeat_interval=settings.worker_heartbeat_interval_seconds,
    )
    worker.work()
