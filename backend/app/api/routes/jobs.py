from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.job import JobResponse
from app.services.jobs import JobService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
def list_jobs(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> list[JobResponse]:
    service = JobService(db)
    return service.list_jobs(user_id=current_user.id, is_admin=current_user.is_admin)

@router.post("/stop")
def stop_user_jobs(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> dict[str, str]:
    from app.worker import cancel_all_jobs
    # This empties the queue entirely. In a multi-tenant system this halts everyone.
    # However, we'll mark only the current user's DB jobs as cancelled.
    cancel_all_jobs()
    
    from app.models.job import Job
    active_jobs = db.query(Job).filter(
        Job.status.in_(["queued", "processing"]),
        Job.user_id == current_user.id
    ).all()
    
    db_cancelled = 0
    for job in active_jobs:
        job.status = "failed"
        job.error_message = "Cancelled by user"
        db_cancelled += 1
    db.commit()

    return {"message": f"Stopped active jobs and cancelled {db_cancelled} database jobs."}

@router.post("/cleanup")
def cleanup_user_jobs(
    older_than_hours: int = 0, 
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user)
) -> dict[str, int]:
    from app.services.cleanup_service import CleanupService
    service = CleanupService(db)
    deleted_jobs = service.cleanup_finished_jobs(older_than_hours=older_than_hours, user_id=current_user.id)
    return {"deleted_jobs": deleted_jobs}

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if not current_user.is_admin and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    return job
