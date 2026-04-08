import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.services.cleanup_service import CleanupService


router = APIRouter(prefix="/admin", tags=["admin"])


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
    current_admin=Depends(get_current_active_admin),
) -> list[dict]:
    root = _get_root(source)
    if not root.exists():
        return []

    results: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        stat = path.stat()
        results.append(
            {
                "source": source,
                "name": path.name,
                "relative_path": str(path.relative_to(root)).replace("\\", "/"),
                "size": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
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
