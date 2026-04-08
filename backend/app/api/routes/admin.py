from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin
from app.db.session import get_db
from app.services.cleanup_service import CleanupService


router = APIRouter(prefix="/admin", tags=["admin"])


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
