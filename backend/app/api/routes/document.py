from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.document import DocumentJobCreateResponse
from app.schemas.job import JobResponse
from app.services.document_service import DOCUMENT_TARGET_FORMATS
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.upload_validation import UploadValidationService
from app.tasks.document_tasks import run_document_conversion
from app.worker import enqueue_job


router = APIRouter(prefix="/document", tags=["document"])


@router.post("/jobs", response_model=DocumentJobCreateResponse)
async def create_document_job(
    file: UploadFile = File(...),
    target_format: str = Query(default="PDF"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> DocumentJobCreateResponse:
    normalized_format = target_format.upper()
    if normalized_format not in DOCUMENT_TARGET_FORMATS:
        raise HTTPException(status_code=400, detail="Unsupported document target format")

    storage_service = StorageService()
    job_service = JobService(db)
    validator = UploadValidationService()

    await validator.validate_file(file, allowed_extensions=storage_service.settings.allowed_document_extensions)
    input_path = await storage_service.persist_upload(file)

    job = job_service.create_job(
        job_type="document",
        original_filename=file.filename or "upload.bin",
        stored_filename=input_path.name,
        input_path=str(input_path),
        user_id=current_user.id,
    )

    enqueue_job(
        run_document_conversion,
        job.id,
        normalized_format,
        job_timeout=storage_service.settings.queue_document_timeout,
        retry_max=1,
        job_type=job.job_type,
    )

    return DocumentJobCreateResponse(
        job_id=job.id,
        status="queued",
        target_format=normalized_format,
        original_filename=job.original_filename,
        output_filename=None,
        download_url=None,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_document_job(job_id: str, db: Session = Depends(get_db)) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "document":
        raise HTTPException(status_code=404, detail="Document job not found")

    return job


@router.get("/jobs/{job_id}/download")
def download_document_result(job_id: str, db: Session = Depends(get_db)) -> FileResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type != "document":
        raise HTTPException(status_code=404, detail="Document job not found")

    if job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=409, detail="Document job is not ready for download")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Converted file is missing")

    clean_name = Path(job.original_filename).stem + "_converted" + output_path.suffix
    return FileResponse(path=output_path, filename=clean_name)
