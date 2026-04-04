from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audio import AudioJobCreateResponse
from app.schemas.job import JobResponse
from app.services.audio_service import AUDIO_BITRATES, AUDIO_FORMATS
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.upload_validation import UploadValidationService
from app.tasks.audio_tasks import run_audio_conversion
from app.worker import enqueue_job


router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/jobs", response_model=AudioJobCreateResponse)
async def create_audio_job(
    file: UploadFile = File(...),
    target_format: str = Query(default="MP3"),
    bitrate: str = Query(default="192k"),
    db: Session = Depends(get_db),
) -> AudioJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in AUDIO_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported audio target format")
    if bitrate not in AUDIO_BITRATES:
        raise HTTPException(status_code=400, detail="Unsupported bitrate")

    storage_service = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()

    await validator.validate_file(file, allowed_extensions=storage_service.settings.allowed_audio_extensions)

    input_path = await storage_service.persist_upload(file)

    job = job_service.create_job(
        job_type="audio",
        original_filename=file.filename or "upload.bin",
        stored_filename=input_path.name,
        input_path=str(input_path),
    )

    enqueue_job(run_audio_conversion, job.id, normalized_format, bitrate, retry_max=1)

    return AudioJobCreateResponse(
        job_id=job.id,
        status="queued",
        target_format=normalized_format,
        bitrate=bitrate,
        original_filename=job.original_filename,
        output_filename=None,
        download_url=None,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_audio_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "audio":
        raise HTTPException(status_code=404, detail="Audio job not found")

    return job


@router.get("/jobs/{job_id}/download")
def download_audio_result(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "audio":
        raise HTTPException(status_code=404, detail="Audio job not found")

    if job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=409, detail="Audio job is not ready for download")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Converted file is missing")

    return FileResponse(path=output_path, filename=output_path.name)
