from pathlib import Path

from app.db.session import SessionLocal
from app.services.image_service import ImageConversionService, IMAGE_FORMAT_MAP
from app.services.jobs import JobService
from app.services.storage import StorageService


def run_image_conversion(job_id: str, target_format: str, quality: int) -> dict[str, str]:
    db = SessionLocal()

    try:
        job_service = JobService(db)
        image_service = ImageConversionService()
        storage_service = StorageService()

        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in IMAGE_FORMAT_MAP:
            raise ValueError(f"Unsupported image target format: {target_format}")

        output_extension = IMAGE_FORMAT_MAP[normalized_format][1]
        output_path = storage_service.build_output_path(Path(job.original_filename).stem, output_extension)

        job_service.mark_processing(job)
        image_service.convert(
            source_path=Path(job.input_path),
            output_path=output_path,
            target_format=normalized_format,
            quality=quality,
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
