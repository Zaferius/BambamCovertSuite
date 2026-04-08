import datetime
import shutil
from pathlib import Path

from app.db.session import SessionLocal
from app.services.audio_service import AUDIO_BITRATES, AUDIO_FORMATS, AudioConversionService
from app.services.document_service import DOCUMENT_TARGET_FORMATS, DocumentConversionService
from app.services.image_service import IMAGE_FORMAT_MAP, ImageConversionService
from app.services.jobs import JobService
from app.services.storage import StorageService
from app.services.video_service import VIDEO_FORMATS, VideoConversionService


def run_batch_image_conversion(job_id: str, file_paths: list[str], target_format: str, quality: int) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        image_service = ImageConversionService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in IMAGE_FORMAT_MAP:
            raise ValueError(f"Unsupported image target format: {target_format}")

        output_dir = storage.build_job_output_dir(job_id)
        ext = IMAGE_FORMAT_MAP[normalized_format][1]
        outputs: list[Path] = []

        job_service.mark_processing(job)
        for index, file_path in enumerate(file_paths, start=1):
            source = Path(file_path)
            
            # Use a cleaner original filename instead of the uuid prefix
            original_name = source.stem
            if len(original_name) > 36 and "-" in original_name:
                parts = original_name.split("_", 1)
                if len(parts) > 1 and len(parts[0]) >= 32:
                    original_name = parts[1]
                    
            output = output_dir / f"{original_name}_converted.{ext}"
            image_service.convert(source_path=source, output_path=output, target_format=normalized_format, quality=quality)
            outputs.append(output)

        bundle_path = storage.build_bundle_path(job_id, "images")
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


def run_batch_audio_conversion(job_id: str, file_paths: list[str], target_format: str, bitrate: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        audio_service = AudioConversionService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio target format: {target_format}")
        if bitrate not in AUDIO_BITRATES:
            raise ValueError(f"Unsupported bitrate: {bitrate}")

        output_dir = storage.build_job_output_dir(job_id)
        outputs: list[Path] = []

        job_service.mark_processing(job)
        for index, file_path in enumerate(file_paths, start=1):
            source = Path(file_path)
            
            original_name = source.stem
            if len(original_name) > 36 and "-" in original_name:
                parts = original_name.split("_", 1)
                if len(parts) > 1 and len(parts[0]) >= 32:
                    original_name = parts[1]
                    
            output = output_dir / f"{original_name}_converted.{normalized_format.lower()}"
            audio_service.convert(source_path=source, output_path=output, target_format=normalized_format, bitrate=bitrate)
            outputs.append(output)

        bundle_path = storage.build_bundle_path(job_id, "audio")
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


def run_batch_video_conversion(
    job_id: str,
    file_paths: list[str],
    target_format: str,
    fps: int,
    resize_enabled: bool,
    width: int | None,
    height: int | None,
) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        video_service = VideoConversionService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in VIDEO_FORMATS:
            raise ValueError(f"Unsupported video target format: {target_format}")

        output_dir = storage.build_job_output_dir(job_id)
        outputs: list[Path] = []

        job_service.mark_processing(job)
        for index, file_path in enumerate(file_paths, start=1):
            source = Path(file_path)
            
            original_name = source.stem
            if len(original_name) > 36 and "-" in original_name:
                parts = original_name.split("_", 1)
                if len(parts) > 1 and len(parts[0]) >= 32:
                    original_name = parts[1]
                    
            output = output_dir / f"{original_name}_converted.{normalized_format.lower()}"
            video_service.convert(
                source_path=source,
                output_path=output,
                target_format=normalized_format,
                fps=fps,
                resize_enabled=resize_enabled,
                width=width,
                height=height,
            )
            outputs.append(output)

        bundle_path = storage.build_bundle_path(job_id, "video")
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


def run_batch_document_conversion(job_id: str, file_paths: list[str], target_format: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        document_service = DocumentConversionService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        normalized_format = target_format.upper()
        if normalized_format not in DOCUMENT_TARGET_FORMATS:
            raise ValueError(f"Unsupported document target format: {target_format}")

        output_dir = storage.build_job_output_dir(job_id)
        outputs: list[Path] = []

        job_service.mark_processing(job)
        for file_path in file_paths:
            source = Path(file_path)
            
            original_name = source.stem
            if len(original_name) > 36 and "-" in original_name:
                parts = original_name.split("_", 1)
                if len(parts) > 1 and len(parts[0]) >= 32:
                    original_name = parts[1]
                    
            output_dir_clean = output_dir / f"{original_name}_converted"
            converted = document_service.convert(source_path=source, output_dir=output_dir, target_format=normalized_format)
            
            if converted and converted.exists():
                new_converted_path = converted.with_name(f"{original_name}_converted{converted.suffix}")
                shutil.move(str(converted), str(new_converted_path))
                converted = new_converted_path
                
            outputs.append(converted)

        bundle_path = storage.build_bundle_path(job_id, "documents")
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


def run_batch_rename(
    job_id: str,
    file_paths: list[str],
    pattern: str,
    start_index: int,
    keep_extension: bool,
) -> dict[str, str]:
    db = SessionLocal()
    try:
        job_service = JobService(db)
        storage = StorageService()
        job = job_service.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        output_dir = storage.build_job_output_dir(job_id)
        outputs: list[Path] = []
        used_names: set[str] = set()
        date_value = datetime.datetime.now().strftime("%Y%m%d")

        job_service.mark_processing(job)

        for index, file_path in enumerate(file_paths, start=1):
            source = Path(file_path)
            base_name = source.stem
            extension = source.suffix.lstrip(".")

            try:
                rendered = pattern.format(
                    name=base_name,
                    ext=extension,
                    index=start_index + index - 1,
                    date=date_value,
                )
            except Exception:
                rendered = f"{base_name}_{start_index + index - 1}"

            rendered = rendered.strip() or f"{base_name}_{start_index + index - 1}"
            final_name = rendered if not keep_extension or not extension else f"{rendered}.{extension}"

            candidate = output_dir / final_name
            if candidate.name.lower() in used_names or candidate.exists():
                stem = candidate.stem
                suffix = candidate.suffix
                duplicate_counter = 1
                while True:
                    duplicate = output_dir / f"{stem}_{duplicate_counter}{suffix}"
                    if duplicate.name.lower() not in used_names and not duplicate.exists():
                        candidate = duplicate
                        break
                    duplicate_counter += 1

            shutil.copy2(source, candidate)
            used_names.add(candidate.name.lower())
            outputs.append(candidate)

        bundle_path = storage.build_bundle_path(job_id, "renamed")
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
