from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.job import JobResponse
from app.schemas.video import VideoJobCreateResponse
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.upload_validation import UploadValidationService
from app.services.video_service import VIDEO_FORMATS, normalize_resize_dimensions
from app.tasks.video_tasks import run_video_conversion
from app.worker import enqueue_job


router = APIRouter(prefix="/video", tags=["video"])


@router.post("/jobs", response_model=VideoJobCreateResponse)
async def create_video_job(
    file: UploadFile = File(...),
    target_format: str = Query(default="MP4"),
    fps: int = Query(default=0, ge=0),
    resize_enabled: bool = Query(default=False),
    width: int | None = Query(default=None, ge=1),
    height: int | None = Query(default=None, ge=1),
    trim_enabled: bool = Query(default=False),
    trim_start: float | None = Query(default=None, ge=0),
    trim_end: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> VideoJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in VIDEO_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported video target format")

    if resize_enabled and (width is None or height is None):
        raise HTTPException(status_code=400, detail="Width and height are required when resize is enabled")

    normalized_width = width
    normalized_height = height
    if resize_enabled:
        normalized_width, normalized_height = normalize_resize_dimensions(width, height)

    if trim_enabled:
        if trim_start is None or trim_end is None:
            raise HTTPException(status_code=400, detail="trim_start and trim_end are required when trim is enabled")
        if trim_end <= trim_start:
            raise HTTPException(status_code=400, detail="trim_end must be greater than trim_start")

    storage_service = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()

    await validator.validate_file(file, allowed_extensions=storage_service.settings.allowed_video_extensions)

    input_path = await storage_service.persist_upload(file)

    job = job_service.create_job(
        job_type="video",
        original_filename=file.filename or "upload.bin",
        stored_filename=input_path.name,
        input_path=str(input_path),
        user_id=current_user.id,
    )

    enqueue_job(
        run_video_conversion,
        job.id,
        normalized_format,
        fps,
        resize_enabled,
        normalized_width,
        normalized_height,
        trim_enabled,
        trim_start,
        trim_end,
        job_timeout=storage_service.settings.queue_video_timeout,
        retry_max=1,
    )

    return VideoJobCreateResponse(
        job_id=job.id,
        status="queued",
        target_format=normalized_format,
        fps=fps,
        resize_enabled=resize_enabled,
        width=normalized_width,
        height=normalized_height,
        trim_enabled=trim_enabled,
        trim_start=trim_start,
        trim_end=trim_end,
        original_filename=job.original_filename,
        output_filename=None,
        download_url=None,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_video_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "video":
        raise HTTPException(status_code=404, detail="Video job not found")

    return job


@router.get("/jobs/{job_id}/download")
def download_video_result(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "video":
        raise HTTPException(status_code=404, detail="Video job not found")

    if job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=409, detail="Video job is not ready for download")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Converted file is missing")

    clean_name = Path(job.original_filename).stem + "_converted" + output_path.suffix
    return FileResponse(path=output_path, filename=clean_name)
