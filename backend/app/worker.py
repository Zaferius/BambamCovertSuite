from redis import Redis
from rq import Queue
from rq import Retry
from rq import Worker

from app.core.config import get_settings


def get_queue() -> Queue:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    return Queue("bambam-jobs", connection=connection)


def enqueue_job(func, *args, **kwargs):
    settings = get_settings()
    timeout = kwargs.pop("job_timeout", settings.queue_default_timeout)
    retry_max = kwargs.pop("retry_max", 1)
    queue = get_queue()
    return queue.enqueue(
        func,
        *args,
        job_timeout=timeout,
        failure_ttl=settings.queue_failure_ttl_seconds,
        result_ttl=settings.queue_result_ttl_seconds,
        retry=Retry(max=retry_max, interval=[10, 30]) if retry_max > 0 else None,
        **kwargs,
    )


if __name__ == "__main__":
    queue = get_queue()
    worker = Worker([queue], connection=queue.connection)
    worker.work()
