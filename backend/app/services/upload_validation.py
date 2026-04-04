from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import get_settings


class UploadValidationService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def validate_file(self, upload: UploadFile, *, allowed_extensions: list[str], max_size_mb: int | None = None) -> None:
        filename = upload.filename or "upload.bin"
        extension = Path(filename).suffix.lower()

        if extension not in {ext.lower() for ext in allowed_extensions}:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: {extension or 'unknown'}")

        max_bytes = (max_size_mb or self.settings.max_upload_size_mb) * 1024 * 1024
        file_obj = upload.file
        current_pos = file_obj.tell()
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(current_pos)

        if size > max_bytes:
            raise HTTPException(status_code=413, detail=f"File exceeds size limit of {max_size_mb or self.settings.max_upload_size_mb} MB")

    async def validate_files(self, uploads: list[UploadFile], *, allowed_extensions: list[str], max_size_mb: int | None = None) -> None:
        for upload in uploads:
            await self.validate_file(upload, allowed_extensions=allowed_extensions, max_size_mb=max_size_mb)
