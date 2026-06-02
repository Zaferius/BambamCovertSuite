from pydantic import BaseModel, Field, HttpUrl


class YouTubeAnalyzeRequest(BaseModel):
    urls: list[str] = Field(min_length=1)
    download_mode: str = Field(default="video")


class YouTubeQualityOption(BaseModel):
    value: str
    label: str
    available: bool = True


class YouTubeAnalysisItem(BaseModel):
    url: str
    normalized_url: str | None = None
    title: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: HttpUrl | None = None
    platform: str | None = None
    available_qualities: list[YouTubeQualityOption] = []
    available_audio_formats: list[str] = []
    status: str
    error_message: str | None = None


class YouTubeAnalyzeResponse(BaseModel):
    items: list[YouTubeAnalysisItem]


class YouTubeJobCreateRequest(BaseModel):
    urls: list[str] = Field(min_length=1)
    download_mode: str = Field(default="video")
    selected_quality: str = Field(default="720p")
    audio_format: str = Field(default="mp3")


class YouTubeJobCreateResponse(BaseModel):
    job_id: str
    status: str
    original_filename: str
    output_filename: str | None = None
    download_url: str | None = None
    item_count: int = 1
    progress: int = 0
    progress_detail: str | None = None


class YouTubeDownloadTokenResponse(BaseModel):
    download_url: str
    expires_in_seconds: int
