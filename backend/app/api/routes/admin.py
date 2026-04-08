import shutil
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


router = APIRouter(prefix="/admin", tags=["admin"])


# ============ Schemas ============
class BotSettingsUpdate(BaseModel):
    telegram_bot_token: str | None = None
    bot_enabled: bool | None = None


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
    row = db.query(BotSettings).first()
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
    row = db.query(BotSettings).first()
    return {"telegram_bot_token": row.telegram_bot_token if row else None}


@router.put("/bot-settings")
def update_bot_settings(
    payload: BotSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_active_admin),
) -> dict:
    row = db.query(BotSettings).first()
    if not row:
        row = BotSettings(id=1)

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
