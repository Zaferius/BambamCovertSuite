from pathlib import Path

from app.db.session import SessionLocal
from app.services.audio_service import AUDIO_FORMATS, AudioConversionService
from app.services.jobs import JobService
from app.services.storage import StorageService


def run_audio_conversion(job_id: str, target_format: str, bitrate: str) -> dict[str, str]:
    db = SessionLocal()

    try:
        job_service = JobService(db)
        audio_service = AudioConversionService()
        storage_service = StorageService()

        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio target format: {target_format}")

        output_path = storage_service.build_output_path(Path(job.original_filename).stem, normalized_format.lower())

        job_service.mark_processing(job)
        audio_service.convert(
            source_path=Path(job.input_path),
            output_path=output_path,
            target_format=normalized_format,
            bitrate=bitrate,
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
