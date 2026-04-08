from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from sqlalchemy import select
from app.models.job import Job
from app.core.config import get_settings
from app.services.jobs import JobService


class CleanupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.job_service = JobService(db)

    def cleanup_finished_jobs(self, older_than_hours: int = 24, user_id: str | None = None) -> int:
        """
        Remove completed or failed jobs older than X hours.
        If user_id is provided, only removes jobs for that user.
        Deletes files (outputs, bundles) and the database records.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        query = select(Job).where(
            Job.status.in_(["completed", "failed"]),
            Job.updated_at <= cutoff
        )
        if user_id:
            query = query.where(Job.user_id == user_id)
            
        jobs_to_delete = self.db.scalars(query).all()
        deleted = 0

        for job in jobs_to_delete:
            for path_value in [job.input_path, job.output_path]:
                if not path_value:
                    continue
                path = Path(path_value)
                if path.exists() and path.is_file():
                    path.unlink(missing_ok=True)

            if job.output_path:
                output_parent = Path(job.output_path).parent
                if output_parent.exists() and output_parent.is_dir() and output_parent != self.settings.output_dir:
                    try:
                        output_parent.rmdir()
                    except OSError:
                        pass

            self.job_service.delete_job(job)
            deleted += 1

        return deleted

    def cleanup_stale_pending_files(self, *, older_than_hours: int = 6) -> int:
        threshold = datetime.utcnow() - timedelta(hours=older_than_hours)  # noqa: DTZ003
        jobs = self.job_service.list_jobs()
        cleaned = 0

        for job in jobs:
            if job.updated_at >= threshold or job.status not in {"queued", "processing"}:
                continue

            input_path = Path(job.input_path)
            if input_path.exists() and input_path.is_file():
                input_path.unlink(missing_ok=True)
                cleaned += 1

            job.status = "failed"
            job.error_message = "Cleaned as stale pending job"
            self.db.add(job)

        self.db.commit()
        return cleaned
