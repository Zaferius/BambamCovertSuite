from pathlib import Path

from fastapi import UploadFile

from app.services.storage import StorageService
from app.services.upload_validation import UploadValidationService


class DummyFile:
    def __init__(self, path: Path) -> None:
        self._handle = path.open("rb")

    def seek(self, *args, **kwargs):
        return self._handle.seek(*args, **kwargs)

    def tell(self):
        return self._handle.tell()


def test_storage_build_bundle_path_contains_job_id() -> None:
    service = StorageService()
    path = service.build_bundle_path("job-123", "results")
    assert "job-123" in path.name
    assert path.suffix == ".zip"


def test_storage_build_job_output_dir_creates_directory() -> None:
    service = StorageService()
    path = service.build_job_output_dir("job-456")
    assert path.exists()
    assert path.is_dir()


async def test_upload_validation_accepts_allowed_extension(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.png"
    file_path.write_bytes(b"fake-image")
    upload = UploadFile(filename="sample.png", file=DummyFile(file_path))
    service = UploadValidationService()
    await service.validate_file(upload, allowed_extensions=[".png"])
