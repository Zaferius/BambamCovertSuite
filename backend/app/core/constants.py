from pathlib import Path

APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Self-hosted media conversion API for the Bambam web application."

LOCALHOST_API_ORIGIN = "http://localhost:3000"

DEFAULT_CORS_ORIGINS = [
    LOCALHOST_API_ORIGIN,
]

DEFAULT_QUEUE_NAME = "bambam-jobs"

DEFAULT_OUTPUT_FILE_SUFFIX = "_converted"
DEFAULT_FALLBACK_UPLOAD_FILENAME = "upload.bin"

DEFAULT_WORKER_STATUS_KEY = "worker_status"
DEFAULT_WORKER_TARGET_COUNT_KEY = "worker_target_count"
DEFAULT_WORKER_SCALE_LOCK_KEY = "worker_scale_lock"

DEFAULT_WORKER_SCALE_COMMAND = "docker-compose"
DEFAULT_WORKER_COMPOSE_FILENAMES = ("docker-compose.yml", "docker-compose.yaml")
DEFAULT_WORKER_COMPOSE_DIR_CANDIDATES = (Path("/workspace"), Path("/app"))
DEFAULT_SANITIZED_SCALE_COMPOSE_PREFIX = "worker-scale-"
DEFAULT_SANITIZED_SCALE_COMPOSE_SUFFIX = ".yaml"
DEFAULT_WORKER_COMPOSE_FILE = "/workspace/docker-compose.yml"
DEFAULT_WORKER_COMPOSE_PROJECT_DIR = "/workspace"

LIBREOFFICE_BINARY = "libreoffice"
LIBREOFFICE_PROFILE_DIR_NAME = "libreoffice_profile"
LIBREOFFICE_TEMP_SOURCE_PREFIX = "document-source-"
LIBREOFFICE_TEMP_OUTPUT_PREFIX = "document-output-"
LIBREOFFICE_LOAD_ERROR_MARKERS = (
    "source file could not be loaded",
    "no export filter",
    "Please verify input parameters",
)

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

