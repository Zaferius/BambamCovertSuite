from pydantic import BaseModel, Field


class ImageJobCreateResponse(BaseModel):
    job_id: str
    status: str
    target_format: str
    quality: int
    original_filename: str
    output_filename: str | None = None
    download_url: str | None = None


class ImageJobRequest(BaseModel):
    target_format: str = Field(default="PNG")
    quality: int = Field(default=90, ge=1, le=100)
