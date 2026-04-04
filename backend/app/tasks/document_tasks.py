from pathlib import Path

from app.db.session import SessionLocal
from app.services.document_service import DOCUMENT_TARGET_FORMATS, DocumentConversionService
from app.services.jobs import JobService
from app.services.storage import StorageService


def run_document_conversion(job_id: str, target_format: str) -> dict[str, str]:
    db = SessionLocal()

    try:
        job_service = JobService(db)
        document_service = DocumentConversionService()
        storage_service = StorageService()

        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in DOCUMENT_TARGET_FORMATS:
            raise ValueError(f"Unsupported document target format: {target_format}")

        output_dir = storage_service.settings.output_dir / job.id

        job_service.mark_processing(job)
        output_path = document_service.convert(
            source_path=Path(job.input_path),
            output_dir=output_dir,
            target_format=normalized_format,
        )
        job_service.mark_completed(job, str(output_path))

        return {
            "job_id": job.id,
            "status": "completed",
            "output_path": str(output_path),
        }
    except Exception as exc:
        job = JobService(db).get_job(job_id)
        if job is not None:
            JobService(db).mark_failed(job, str(exc))
        raise
    finally:
        db.close()
