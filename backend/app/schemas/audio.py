from pydantic import BaseModel, Field


class AudioJobCreateResponse(BaseModel):
    job_id: str
    status: str
    target_format: str
    bitrate: str
    original_filename: str
    output_filename: str | None = None
    download_url: str | None = None


class AudioJobRequest(BaseModel):
    target_format: str = Field(default="MP3")
    bitrate: str = Field(default="192k")
