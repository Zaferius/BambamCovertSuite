import shutil
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.models.bot_settings import BotSettings
from app.services.cleanup_service import CleanupService
from app.worker import (
    WORKER_SCALE_LOCK_KEY,
    get_queue,
    get_worker_target_count,
    list_worker_statuses,
    set_worker_target_count,
)


router = APIRouter(prefix="/admin", tags=["admin"])


# ============ Schemas ============
class BotSettingsUpdate(BaseModel):
    telegram_bot_token: str | None = None
    bot_enabled: bool | None = None


class WorkerScaleRequest(BaseModel):
    target_count: int


def _resolve_worker_health(
    workers: list[dict],
    queue_size: int,
    expected_workers: int,
    api_ok: bool,
    redis_ok: bool,
) -> str:
    if not api_ok or not redis_ok:
        return "down"
    online_workers = [w for w in workers if w.get("online")]
    if not online_workers:
        return "down"
    if expected_workers > 0 and len(online_workers) < expected_workers:
        return "degraded"
    if queue_size > 0 and not any(w.get("status") == "busy" for w in online_workers):
        return "degraded"
    return "healthy!"


def _list_workers_with_online_flag() -> tuple[list[dict], int, int, int]:
    settings = get_settings()
    now = int(time.time())
    threshold = settings.worker_offline_threshold_seconds
    workers = list_worker_statuses()

    # Stable, human-friendly naming in dashboard: Worker 1, Worker 2, ...
    # We compute names from start-time order to keep labels predictable.
    ordered_for_naming = sorted(
        workers,
        key=lambda w: (
            int(w.get("started_at", 0) or 0),
            str(w.get("worker_id", "")),
        ),
    )
    for index, worker in enumerate(ordered_for_naming, start=1):
        worker["display_name"] = f"Worker {index}"

    for worker in workers:
        # Defensive default: if last_seen is absent on any legacy payload,
        # treat started_at/now as heartbeat baseline so ready workers are
        # shown as online + idle instead of immediately offline.
        raw_last_seen = worker.get("last_seen", worker.get("started_at", now))
        last_seen = int(raw_last_seen or now)
        worker["online"] = (now - last_seen) <= threshold
        worker["status"] = worker.get("status", "idle")
        if not worker["online"]:
            worker["status"] = "offline"
        elif worker["status"] not in {"busy", "idle"}:
            worker["status"] = "idle"

    online_count = sum(1 for w in workers if w.get("online"))
    busy_count = sum(1 for w in workers if w.get("online") and w.get("status") == "busy")
    idle_count = sum(1 for w in workers if w.get("online") and w.get("status") == "idle")
    workers.sort(key=lambda w: (not w.get("online"), w.get("display_name", ""), w.get("worker_id", "")))
    return workers, online_count, busy_count, idle_count


def _queue_size() -> int:
    try:
        return len(get_queue())
    except Exception:
        return 0


def _redis_health() -> bool:
    try:
        return bool(get_queue().connection.ping())
    except Exception:
        return False


def _run_compose_scale(target_count: int) -> tuple[int, str]:
    settings = get_settings()
    command_prefix = shlex.split(settings.worker_scale_command or "")
    if not command_prefix:
        return 1, "WORKER_SCALE_COMMAND is empty"

    configured_compose_file = (settings.worker_compose_file or "").strip()
    configured_project_dir = (settings.worker_compose_project_dir or "").strip()

    compose_candidates: list[Path] = []
    if configured_compose_file:
        compose_candidates.append(Path(configured_compose_file))
    compose_candidates.extend(
        [
            Path("/workspace/docker-compose.yml"),
            Path("/workspace/docker-compose.yaml"),
            Path("/app/docker-compose.yml"),
            Path("/app/docker-compose.yaml"),
        ]
    )

    compose_file_path: Path | None = None
    for candidate in compose_candidates:
        if candidate.exists() and candidate.is_file():
            compose_file_path = candidate
            break

    if compose_file_path is None:
        return 1, (
            "Compose file not found. Checked: "
            + ", ".join(str(p) for p in compose_candidates)
        )

    project_dir = configured_project_dir or str(compose_file_path.parent)

    command = [
        *command_prefix,
        "-f",
        str(compose_file_path),
        "up",
        "-d",
        "--no-deps",
        "--scale",
        f"worker={target_count}",
        "worker",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=settings.worker_scale_timeout_seconds,
            check=False,
        )
        combined = (result.stdout or "")
        if result.stderr:
            combined = f"{combined}\n{result.stderr}".strip()
        return result.returncode, combined[:4000]
    except FileNotFoundError as exc:
        return 1, f"Scale command executable not found: {exc}"
    except subprocess.TimeoutExpired as exc:
        return 1, (
            f"Scale command timed out after {settings.worker_scale_timeout_seconds}s: "
            f"{exc}"
        )
    except Exception as exc:
        return 1, f"Unexpected scale command error: {exc}"


# ============ Bot Settings Endpoints ============
def _mask_token(token: str | None) -> str | None:
    """Mask sensitive token for API responses (show first 8 chars + *****)."""
    if not token or len(token) < 8:
        return None
    return f"{token[:8]}****"


@router.get("/bot-settings")
def get_bot_settings(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict:
    """Get the legacy (singleton) bot settings for backward compatibility."""
    row = db.query(BotSettings).filter(BotSettings.user_id == None).first()
    if not row:
        return {
            "telegram_bot_token": None,
            "bot_enabled": False,
            "has_token": False,
        }
    return {
        "telegram_bot_token": _mask_token(row.telegram_bot_token),
        "bot_enabled": row.bot_enabled,
        "has_token": bool(row.telegram_bot_token),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/bot-settings/token")
def get_bot_token_raw(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict:
    """Returns raw (unmasked) token — used by the bot service at startup."""
    row = db.query(BotSettings).filter(BotSettings.user_id == None).first()
    return {"telegram_bot_token": row.telegram_bot_token if row else None}


@router.get("/bot-settings/active")
def get_active_bots(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> list[dict]:
    """Get all active bot settings with user information."""
    rows = db.query(BotSettings, User.username).outerjoin(
        User, BotSettings.user_id == User.id
    ).filter(BotSettings.bot_enabled == True).all()

    result = []
    for bot_settings, username in rows:
        result.append({
            "id": bot_settings.id,
            "user_id": bot_settings.user_id,
            "username": username or "System (Legacy)",
            "has_token": bool(bot_settings.telegram_bot_token),
            "bot_enabled": bot_settings.bot_enabled,
            "updated_at": bot_settings.updated_at.isoformat() if bot_settings.updated_at else None,
        })

    return result


@router.put("/bot-settings")
def update_bot_settings(
    payload: BotSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict:
    """Update the legacy (singleton) bot settings."""
    row = db.query(BotSettings).filter(BotSettings.user_id == None).first()
    if not row:
        row = BotSettings(user_id=None)

    if payload.telegram_bot_token is not None:
        row.telegram_bot_token = payload.telegram_bot_token if payload.telegram_bot_token else None
    if payload.bot_enabled is not None:
        row.bot_enabled = payload.bot_enabled

    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "message": "Bot settings updated",
        "bot_enabled": row.bot_enabled,
        "has_token": bool(row.telegram_bot_token),
    }


@router.get("/workers")
def list_workers(current_admin=Depends(get_current_active_admin)) -> dict:
    workers, online_count, busy_count, idle_count = _list_workers_with_online_flag()
    queue_size = _queue_size()
    target_count = get_worker_target_count()
    redis_ok = _redis_health()
    health = _resolve_worker_health(
        workers,
        queue_size,
        target_count,
        api_ok=True,
        redis_ok=redis_ok,
    )
    return {
        "workers": workers,
        "summary": {
            "target_workers": target_count,
            "online_workers": online_count,
            "busy_workers": busy_count,
            "idle_workers": idle_count,
            "queue_size": queue_size,
            "health": health,
            "api_ok": True,
            "redis_ok": redis_ok,
        },
    }


@router.post("/workers/scale")
def scale_workers(payload: WorkerScaleRequest, current_admin=Depends(get_current_active_admin)) -> dict:
    settings = get_settings()
    if not settings.worker_scale_enabled:
        raise HTTPException(status_code=503, detail="Worker scaling is disabled")

    if payload.target_count < settings.worker_min_count or payload.target_count > settings.worker_max_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"target_count must be between {settings.worker_min_count} and "
                f"{settings.worker_max_count}"
            ),
        )

    conn = get_queue().connection
    lock_ok = conn.set(WORKER_SCALE_LOCK_KEY, "1", nx=True, ex=60)
    if not lock_ok:
        raise HTTPException(status_code=409, detail="Another scaling operation is in progress")

    try:
        code, output = _run_compose_scale(payload.target_count)
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Scale command failed: {output or 'unknown error'}")
        set_worker_target_count(payload.target_count)
        return {
            "message": "Workers scaled successfully",
            "target_workers": payload.target_count,
            "command_output": output,
        }
    finally:
        conn.delete(WORKER_SCALE_LOCK_KEY)


# ============ Utility Functions ============
def _get_root(source: str) -> Path:
    settings = get_settings()
    if source == "outputs":
        return settings.output_dir.resolve()
    if source == "uploads":
        return settings.upload_dir.resolve()
    raise HTTPException(status_code=400, detail="Unsupported source. Use 'outputs' or 'uploads'.")


def _safe_resolve(root: Path, relative_path: str) -> Path:
    if not relative_path or relative_path.strip() == "":
        raise HTTPException(status_code=400, detail="Path is required")
    requested = (root / relative_path).resolve()
    if root != requested and root not in requested.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
    return requested


def _delete_root_contents(root: Path) -> int:
    if not root.exists():
        return 0

    deleted_count = 0
    for target in root.iterdir():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
        deleted_count += 1
    return deleted_count


@router.post("/stop-all-jobs")
def stop_all_jobs(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict[str, str]:
    from app.worker import cancel_all_jobs
    
    # Custom helper function to empty queues
    cancelled_count = cancel_all_jobs()
    
    # Also mark all pending/processing jobs as failed in DB
    from app.models.job import Job
    active_jobs = db.query(Job).filter(Job.status.in_(["queued", "processing"])).all()
    db_cancelled = 0
    for job in active_jobs:
        job.status = "failed"
        job.error_message = "Cancelled by admin"
        db_cancelled += 1
    db.commit()

    return {"message": f"Emptied {cancelled_count} from queue and cancelled {db_cancelled} database jobs."}

@router.post("/cleanup")
def trigger_cleanup(
    older_than_hours: int = Query(default=24, ge=0), 
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict[str, int]:
    service = CleanupService(db)
    deleted_jobs = service.cleanup_finished_jobs(older_than_hours=older_than_hours)
    stale_cleaned = service.cleanup_stale_pending_files(older_than_hours=max(1, older_than_hours // 4))
    return {"deleted_jobs": deleted_jobs, "stale_jobs_cleaned": stale_cleaned}


@router.get("/files")
def list_files(
    source: str = Query(default="outputs"),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> list[dict]:
    root = _get_root(source)
    if not root.exists():
        return []

    users = db.query(User.id, User.username).all()
    user_map = {user_id: username for user_id, username in users}

    jobs = db.query(Job.id, Job.user_id, Job.input_path, Job.output_path, Job.bundle_path).all()
    owner_by_path: dict[str, str] = {}
    owner_by_job_id: dict[str, str] = {}

    for job_id, user_id, input_path, output_path, bundle_path in jobs:
        owner = user_map.get(user_id, "Unknown") if user_id else "Unknown"
        owner_by_job_id[job_id] = owner

        if output_path:
            owner_by_path[Path(output_path).resolve().as_posix()] = owner
        if bundle_path:
            owner_by_path[Path(bundle_path).resolve().as_posix()] = owner
        if input_path:
            for entry in input_path.splitlines():
                if entry.strip():
                    owner_by_path[Path(entry.strip()).resolve().as_posix()] = owner

    results: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        stat = path.stat()
        path_key = path.resolve().as_posix()
        relative_path = str(path.relative_to(root)).replace("\\", "/")
        owner_username = owner_by_path.get(path_key)

        if owner_username is None and source == "outputs":
            first_segment = relative_path.split("/", 1)[0]
            owner_username = owner_by_job_id.get(first_segment)
            if owner_username is None and "_" in path.name:
                maybe_job_id = path.name.split("_", 1)[0]
                owner_username = owner_by_job_id.get(maybe_job_id)

        if owner_username is None:
            owner_username = "Unknown"

        results.append(
            {
                "source": source,
                "name": path.name,
                "relative_path": relative_path,
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "owner_username": owner_username,
            }
        )

    results.sort(key=lambda x: x["modified_at"], reverse=True)
    return results[:limit]


@router.get("/files/view")
def view_file(
    source: str = Query(default="outputs"),
    path: str = Query(...),
    current_admin=Depends(get_current_active_admin),
) -> FileResponse:
    root = _get_root(source)
    target = _safe_resolve(root, path)

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=target, filename=target.name)


@router.delete("/files")
def delete_file(
    source: str = Query(default="outputs"),
    path: str = Query(...),
    current_admin=Depends(get_current_active_admin),
) -> dict[str, str]:
    root = _get_root(source)
    target = _safe_resolve(root, path)

    if not target.exists():
        raise HTTPException(status_code=404, detail="File or folder not found")

    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink(missing_ok=True)

    return {"message": "Deleted"}


@router.delete("/files/all")
def delete_all_files(current_admin=Depends(get_current_active_admin)) -> dict[str, int]:
    settings = get_settings()
    deleted_outputs = _delete_root_contents(settings.output_dir.resolve())
    deleted_uploads = _delete_root_contents(settings.upload_dir.resolve())
    return {
        "deleted_outputs": deleted_outputs,
        "deleted_uploads": deleted_uploads,
        "total_deleted": deleted_outputs + deleted_uploads,
    }
