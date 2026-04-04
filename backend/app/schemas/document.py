from pydantic import BaseModel, Field


class DocumentJobCreateResponse(BaseModel):
    job_id: str
    status: str
    target_format: str
    original_filename: str
    output_filename: str | None = None
    download_url: str | None = None


class DocumentJobRequest(BaseModel):
    target_format: str = Field(default="PDF")
