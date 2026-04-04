from pydantic import BaseModel


class BatchJobCreateResponse(BaseModel):
    job_id: str
    status: str
    item_count: int
    output_filename: str | None = None
    download_url: str | None = None
