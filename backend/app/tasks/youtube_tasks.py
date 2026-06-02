from pathlib import Path

from app.db.session import SessionLocal
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.youtube_service import YouTubeService


def run_youtube_download(job_id: str, urls: list[str], download_mode: str, selected_quality: str, audio_format: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        youtube = YouTubeService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        output_dir = storage.build_job_output_dir(job_id)
        outputs: list[Path] = []
        job_service.mark_processing(job)

        for index, url in enumerate(urls, start=1):
            progress = 10 + int((index - 1) / max(len(urls), 1) * 80)
            job_service.update_progress(job, progress, f"Downloading item {index}/{len(urls)}")
            output_path, resolved_quality = youtube.download_item(url, output_dir, download_mode, selected_quality, audio_format)
            outputs.append(output_path)
            job_service.update_progress(job, min(95, progress + 10), f"Downloaded item {index}/{len(urls)} at {resolved_quality}")

        if len(outputs) == 1:
            job_service.mark_completed(job, str(outputs[0]))
            return {"job_id": job.id, "output_path": str(outputs[0])}

        bundle_path = storage.build_bundle_path(job_id, "youtube")
        job_service.update_progress(job, 96, "Creating zip bundle")
        storage.create_zip_bundle(bundle_path, outputs)
        job_service.mark_completed_with_bundle(job, str(bundle_path), bundle_path.name)
        return {"job_id": job.id, "bundle_path": str(bundle_path)}
    except Exception as exc:
        job = JobService(db).get_job(job_id)
        if job is not None:
            JobService(db).mark_failed(job, str(exc))
        raise
    finally:
        db.close()
