from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "Bambam Converter Suite Web"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    redis_url: str = "redis://redis:6379/0"
    database_url: str = f"sqlite:///{(DATA_DIR / 'db' / 'bambam_web.db').as_posix()}"
    upload_dir: Path = DATA_DIR / "uploads"
    output_dir: Path = DATA_DIR / "outputs"
    temp_dir: Path = DATA_DIR / "temp"
    max_upload_size_mb: int = 250
    allowed_image_extensions: list[str] = Field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"])
    allowed_audio_extensions: list[str] = Field(default_factory=lambda: [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"])
    allowed_video_extensions: list[str] = Field(default_factory=lambda: [".mp4", ".mov", ".mkv", ".avi", ".webm", ".gif"])
    allowed_document_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"])
    queue_default_timeout: str = "30m"
    queue_video_timeout: str = "120m"
    queue_document_timeout: str = "60m"
    queue_result_ttl_seconds: int = 86400
    queue_failure_ttl_seconds: int = 604800

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "db").mkdir(parents=True, exist_ok=True)
    return settings
