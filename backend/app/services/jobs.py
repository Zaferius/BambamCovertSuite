from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        *,
        job_type: str,
        original_filename: str,
        stored_filename: str,
        input_path: str,
        user_id: str | None = None,
    ) -> Job:
        job = Job(
            user_id=user_id,
            job_type=job_type,
            status="queued",
            original_filename=original_filename,
            stored_filename=stored_filename,
            input_path=input_path,
            progress=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(self, user_id: str | None = None, is_admin: bool = False) -> list[Job]:
        query = select(Job)
        if not is_admin and user_id:
            query = query.filter(Job.user_id == user_id)
        return list(self.db.scalars(query.order_by(Job.created_at.desc())).all())

    def get_job(self, job_id: str) -> Job | None:
        return self.db.get(Job, job_id)

    def mark_processing(self, job: Job) -> Job:
        job.status = "processing"
        job.progress = 10
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(self, job: Job, output_path: str) -> Job:
        job.status = "completed"
        job.progress = 100
        job.output_path = output_path
        job.output_filename = output_path.split("/")[-1].split("\\")[-1]
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed_with_bundle(self, job: Job, bundle_path: str, output_filename: str) -> Job:
        job.status = "completed"
        job.progress = 100
        job.bundle_path = bundle_path
        job.output_filename = output_filename
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job: Job) -> None:
        self.db.delete(job)
        self.db.commit()

    def mark_failed(self, job: Job, message: str) -> Job:
        job.status = "failed"
        job.error_message = message
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
