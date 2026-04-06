from pydantic import BaseModel, Field


class VideoJobCreateResponse(BaseModel):
    job_id: str
    status: str
    target_format: str
    fps: int
    resize_enabled: bool
    width: int | None = None
    height: int | None = None
    trim_enabled: bool = False
    trim_start: float | None = None
    trim_end: float | None = None
    original_filename: str
    output_filename: str | None = None
    download_url: str | None = None


class VideoJobRequest(BaseModel):
    target_format: str = Field(default="MP4")
    fps: int = Field(default=0, ge=0)
    resize_enabled: bool = Field(default=False)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    trim_enabled: bool = Field(default=False)
    trim_start: float | None = Field(default=None, ge=0)
    trim_end: float | None = Field(default=None, ge=0)
