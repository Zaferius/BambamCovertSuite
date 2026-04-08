from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.batch import BatchJobCreateResponse
from app.schemas.job import JobResponse
from app.services.audio_service import AUDIO_BITRATES, AUDIO_FORMATS
from app.services.document_service import DOCUMENT_TARGET_FORMATS
from app.services.image_service import IMAGE_FORMAT_MAP
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.upload_validation import UploadValidationService
from app.services.video_service import VIDEO_FORMATS, normalize_resize_dimensions
from app.tasks.batch_tasks import (
    run_batch_rename,
    run_batch_audio_conversion,
    run_batch_document_conversion,
    run_batch_image_conversion,
    run_batch_video_conversion,
)
from app.worker import enqueue_job


router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/image/jobs", response_model=BatchJobCreateResponse)
async def create_batch_image_job(
    files: list[UploadFile] = File(...),
    target_format: str = Query(default="PNG"),
    quality: int = Query(default=90, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> BatchJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in IMAGE_FORMAT_MAP:
        raise HTTPException(status_code=400, detail="Unsupported image target format")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    storage = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()
    await validator.validate_files(files, allowed_extensions=storage.settings.allowed_image_extensions)
    paths = await storage.persist_uploads(files)

    job = job_service.create_job(
        job_type="batch_image",
        original_filename=f"{len(files)} files",
        stored_filename=paths[0].name,
        input_path="\n".join(str(path) for path in paths),
        user_id=current_user.id,
    )

    enqueue_job(run_batch_image_conversion, job.id, [str(path) for path in paths], normalized_format, quality, retry_max=1)

    return BatchJobCreateResponse(job_id=job.id, status="queued", item_count=len(files))


@router.post("/video/jobs", response_model=BatchJobCreateResponse)
async def create_batch_video_job(
    files: list[UploadFile] = File(...),
    target_format: str = Query(default="MP4"),
    fps: int = Query(default=0, ge=0),
    resize_enabled: bool = Query(default=False),
    width: int | None = Query(default=None, ge=1),
    height: int | None = Query(default=None, ge=1),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in VIDEO_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported video target format")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if resize_enabled and (width is None or height is None):
        raise HTTPException(status_code=400, detail="Width and height are required when resize is enabled")

    normalized_width = width
    normalized_height = height
    if resize_enabled:
        normalized_width, normalized_height = normalize_resize_dimensions(width, height)

    storage = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()
    await validator.validate_files(files, allowed_extensions=storage.settings.allowed_video_extensions)
    paths = await storage.persist_uploads(files)

    job = job_service.create_job(
        job_type="batch_video",
        original_filename=f"{len(files)} files",
        stored_filename=paths[0].name,
        input_path="\n".join(str(path) for path in paths),
        user_id=current_user.id,
    )

    enqueue_job(
        run_batch_video_conversion,
        job.id,
        [str(path) for path in paths],
        normalized_format,
        fps,
        resize_enabled,
        normalized_width,
        normalized_height,
        job_timeout=storage.settings.queue_video_timeout,
        retry_max=1,
    )

    return BatchJobCreateResponse(job_id=job.id, status="queued", item_count=len(files))


@router.post("/document/jobs", response_model=BatchJobCreateResponse)
async def create_batch_document_job(
    files: list[UploadFile] = File(...),
    target_format: str = Query(default="PDF"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> BatchJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in DOCUMENT_TARGET_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported document target format")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    storage = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()
    await validator.validate_files(files, allowed_extensions=storage.settings.allowed_document_extensions)
    paths = await storage.persist_uploads(files)

    job = job_service.create_job(
        job_type="batch_document",
        original_filename=f"{len(files)} files",
        stored_filename=paths[0].name,
        input_path="\n".join(str(path) for path in paths),
        user_id=current_user.id,
    )

    enqueue_job(
        run_batch_document_conversion,
        job.id,
        [str(path) for path in paths],
        normalized_format,
        job_timeout=storage.settings.queue_document_timeout,
        retry_max=1,
    )

    return BatchJobCreateResponse(job_id=job.id, status="queued", item_count=len(files))


@router.post("/audio/jobs", response_model=BatchJobCreateResponse)
async def create_batch_audio_job(
    files: list[UploadFile] = File(...),
    target_format: str = Query(default="MP3"),
    bitrate: str = Query(default="192k"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> BatchJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in AUDIO_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported audio target format")
    if bitrate not in AUDIO_BITRATES:
        raise HTTPException(status_code=400, detail="Unsupported bitrate")
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    storage = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()
    await validator.validate_files(files, allowed_extensions=storage.settings.allowed_audio_extensions)
    paths = await storage.persist_uploads(files)

    job = job_service.create_job(
        job_type="batch_audio",
        original_filename=f"{len(files)} files",
        stored_filename=paths[0].name,
        input_path="\n".join(str(path) for path in paths),
        user_id=current_user.id,
    )

    enqueue_job(run_batch_audio_conversion, job.id, [str(path) for path in paths], normalized_format, bitrate, retry_max=1)

    return BatchJobCreateResponse(job_id=job.id, status="queued", item_count=len(files))


@router.post("/rename/jobs", response_model=BatchJobCreateResponse)
async def create_batch_rename_job(
    files: list[UploadFile] = File(...),
    pattern: str = Query(default="{name}_{index}"),
    start_index: int = Query(default=1, ge=0),
    keep_extension: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> BatchJobCreateResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    storage = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()

    inferred_extensions = {
        (Path(upload.filename or "upload.bin").suffix.lower() or "")
        for upload in files
    }
    await validator.validate_files(files, allowed_extensions=list(inferred_extensions))

    paths = await storage.persist_uploads(files)

    job = job_service.create_job(
        job_type="batch_rename",
        original_filename=f"{len(files)} files",
        stored_filename=paths[0].name,
        input_path="\n".join(str(path) for path in paths),
        user_id=current_user.id,
    )

    enqueue_job(
        run_batch_rename,
        job.id,
        [str(path) for path in paths],
        pattern,
        start_index,
        keep_extension,
        retry_max=1,
    )

    return BatchJobCreateResponse(job_id=job.id, status="queued", item_count=len(files))


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_batch_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> JobResponse:
    job = JobService(db).get_job(job_id)
    if job is None or job.job_type not in {"batch_image", "batch_audio", "batch_video", "batch_document", "batch_rename"}:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return job


@router.get("/jobs/{job_id}/download")
def download_batch_bundle(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    job = JobService(db).get_job(job_id)
    if job is None or job.job_type not in {"batch_image", "batch_audio", "batch_video", "batch_document", "batch_rename"}:
        raise HTTPException(status_code=404, detail="Batch job not found")
    if job.status != "completed" or not job.bundle_path:
        raise HTTPException(status_code=409, detail="Batch job is not ready for download")
    return FileResponse(path=job.bundle_path, filename=job.output_filename or "results.zip")
