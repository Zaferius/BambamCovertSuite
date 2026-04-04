from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import UploadFile

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_upload_path(self, original_name: str) -> Path:
        safe_name = Path(original_name).name
        return self.settings.upload_dir / f"{uuid4()}_{safe_name}"

    def build_output_path(self, stem: str, extension: str) -> Path:
        normalized_extension = extension.lower().lstrip(".")
        return self.settings.output_dir / f"{uuid4()}_{stem}.{normalized_extension}"

    def build_job_output_dir(self, job_id: str) -> Path:
        path = self.settings.output_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def build_bundle_path(self, job_id: str, stem: str = "results") -> Path:
        return self.settings.output_dir / f"{job_id}_{stem}.zip"

    def create_zip_bundle(self, bundle_path: Path, files: list[Path]) -> Path:
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(bundle_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in files:
                archive.write(file_path, arcname=file_path.name)
        return bundle_path

    async def persist_upload(self, upload: UploadFile) -> Path:
        destination = self.build_upload_path(upload.filename or "upload.bin")

        with destination.open("wb") as target:
            while chunk := await upload.read(1024 * 1024):
                target.write(chunk)

        await upload.close()
        return destination

    async def persist_uploads(self, uploads: list[UploadFile]) -> list[Path]:
        paths: list[Path] = []
        for upload in uploads:
            paths.append(await self.persist_upload(upload))
        return paths
