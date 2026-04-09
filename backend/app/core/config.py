from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    DEFAULT_CORS_ORIGINS,
    DEFAULT_WORKER_COMPOSE_FILE,
    DEFAULT_WORKER_COMPOSE_PROJECT_DIR,
    DEFAULT_WORKER_SCALE_COMMAND,
)


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "Bambam Converter Suite Web"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    redis_url: str = "redis://redis:6379/0"
    database_url: str = f"sqlite:///{(DATA_DIR / 'db' / 'bambam_web.db').as_posix()}"
    upload_dir: Path = DATA_DIR / "uploads"
    output_dir: Path = DATA_DIR / "outputs"
    temp_dir: Path = DATA_DIR / "temp"
    max_upload_size_mb: int = 250
    allowed_image_extensions: list[str] = Field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".ico"])
    allowed_audio_extensions: list[str] = Field(default_factory=lambda: [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff", ".aif"])
    allowed_video_extensions: list[str] = Field(default_factory=lambda: [".mp4", ".mov", ".mkv", ".avi", ".webm", ".gif", ".wmv", ".flv"])
    allowed_document_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"])
    queue_default_timeout: str = "30m"
    queue_video_timeout: str = "120m"
    queue_document_timeout: str = "60m"
    queue_result_ttl_seconds: int = 86400
    queue_failure_ttl_seconds: int = 604800
    worker_heartbeat_interval_seconds: int = 5
    worker_offline_threshold_seconds: int = 15
    worker_scale_enabled: bool = True
    worker_scale_command: str = DEFAULT_WORKER_SCALE_COMMAND
    worker_compose_file: str = DEFAULT_WORKER_COMPOSE_FILE
    worker_compose_project_dir: str = DEFAULT_WORKER_COMPOSE_PROJECT_DIR
    worker_scale_timeout_seconds: int = 120
    worker_min_count: int = 1
    worker_max_count: int = 8
    worker_target_default: int = 1

    secret_key: str = "bambam-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    admin_username: str = "admin"
    admin_password: str = "bambam123"

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
