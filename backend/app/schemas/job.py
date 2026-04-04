from datetime import datetime

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    original_filename: str
    stored_filename: str
    output_path: str | None
    bundle_path: str | None
    output_filename: str | None
    error_message: str | None
    progress: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
