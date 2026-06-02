from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import DEFAULT_OUTPUT_FILE_SUFFIX, JOB_STATUS_COMPLETED, JOB_STATUS_QUEUED
from app.db.session import get_db
from app.schemas.job import JobResponse
from app.schemas.youtube import YouTubeAnalyzeRequest, YouTubeAnalyzeResponse, YouTubeJobCreateRequest, YouTubeJobCreateResponse
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.youtube_service import YouTubeService
from app.tasks.youtube_tasks import run_youtube_download
from app.worker import enqueue_job


router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.post("/analyze", response_model=YouTubeAnalyzeResponse)
def analyze_youtube_urls(payload: YouTubeAnalyzeRequest, current_user=Depends(get_current_user)) -> YouTubeAnalyzeResponse:
    service = YouTubeService()
    items = service.analyze_urls(payload.urls, payload.download_mode)
    return YouTubeAnalyzeResponse(items=items)


@router.post("/jobs", response_model=YouTubeJobCreateResponse)
def create_youtube_job(
    payload: YouTubeJobCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> YouTubeJobCreateResponse:
    service = YouTubeService()
    urls = service.normalize_urls(payload.urls)
    if not urls:
        raise HTTPException(status_code=400, detail="At least one valid YouTube URL is required")

    normalized_mode = service.validate_mode(payload.download_mode)
    normalized_audio_format = service.validate_audio_format(payload.audio_format)
    job_service = JobService(db)
    storage_service = StorageService()
    parsed = urlparse(urls[0])
    first_video_id = parse_qs(parsed.query).get("v", [None])[0]
    label = first_video_id or Path(parsed.path).name or "youtube-download"
    job_type = "youtube_batch" if len(urls) > 1 else "youtube"
    job = job_service.create_job(
        job_type=job_type,
        original_filename=label,
        stored_filename=storage_service.build_virtual_input_name(job_type, "txt"),
        input_path="\n".join(urls),
        user_id=current_user.id,
    )

    enqueue_job(
        run_youtube_download,
        job.id,
        urls,
        normalized_mode,
        payload.selected_quality,
        normalized_audio_format,
        retry_max=1,
        job_type=job.job_type,
    )

    return YouTubeJobCreateResponse(
        job_id=job.id,
        status=JOB_STATUS_QUEUED,
        original_filename=job.original_filename,
        output_filename=None,
        download_url=None,
        item_count=len(urls),
        progress=0,
        progress_detail="Queued",
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_youtube_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> JobResponse:
    service = JobService(db)
    job = service.get_job(job_id)
    if job is None or job.job_type not in {"youtube", "youtube_batch"}:
        raise HTTPException(status_code=404, detail="YouTube job not found")
    return job


@router.get("/jobs/{job_id}/download")
def download_youtube_result(job_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> FileResponse:
    service = JobService(db)
    job = service.get_job(job_id)

    if job is None or job.job_type not in {"youtube", "youtube_batch"}:
        raise HTTPException(status_code=404, detail="YouTube job not found")

    if job.status != JOB_STATUS_COMPLETED:
        raise HTTPException(status_code=409, detail="YouTube job is not ready for download")

    if job.bundle_path:
        bundle_path = Path(job.bundle_path)
        if not bundle_path.exists():
            raise HTTPException(status_code=404, detail="Downloaded bundle is missing")
        return FileResponse(path=bundle_path, filename=bundle_path.name)

    if not job.output_path:
        raise HTTPException(status_code=404, detail="Downloaded file is missing")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Downloaded file is missing")

    clean_name = Path(job.original_filename).stem + DEFAULT_OUTPUT_FILE_SUFFIX + output_path.suffix
    return FileResponse(path=output_path, filename=clean_name)
