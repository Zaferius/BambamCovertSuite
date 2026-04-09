"""
API client for communicating with the Bambam FastAPI backend.

Handles authentication (OAuth2 login → JWT Bearer token) and job lifecycle:
  - Job creation (image / audio / video / document)
  - Job status polling
  - Output file download
"""

import asyncio
import os
from typing import Optional

import httpx

DOCUMENT_FORMATS = {"PDF", "DOCX", "ODT", "TXT"}
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

DEFAULT_API_BASE_URL = "http://api:8000"
DEFAULT_BOT_API_USERNAME = "admin"
DEFAULT_BOT_API_PASSWORD = "bambam123"
DEFAULT_HTTP_TIMEOUT_SECONDS = 30
DEFAULT_DOWNLOAD_TIMEOUT_SECONDS = 300
DEFAULT_JOB_POLL_INTERVAL_SECONDS = 3.0
DEFAULT_JOB_POLL_MAX_WAIT_SECONDS = 600.0
DEFAULT_OUTPUT_FILENAME = "output"
AUTH_RETRY_ATTEMPTS = 2
AUTH_LOGIN_PATH = "/auth/login"
BOT_TOKEN_PATH = "/admin/bot-settings/token"

API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)
BOT_API_USERNAME = os.getenv("BOT_API_USERNAME", DEFAULT_BOT_API_USERNAME)
BOT_API_PASSWORD = os.getenv("BOT_API_PASSWORD", DEFAULT_BOT_API_PASSWORD)

# Shared token state
_token: Optional[str] = None
_token_lock = asyncio.Lock()

JOB_TYPE_ROUTES = {
    "image": "image",
    "audio": "audio",
    "video": "video",
    "document": "document",
}

SUPPORTED_FORMATS = {
    "image": {"PNG", "JPG", "WEBP", "TIFF", "BMP", "GIF", "ICO"},
    "audio": {"MP3", "WAV", "FLAC", "OGG", "M4A", "AAC", "WMA", "OPUS", "AIFF"},
    "video": {"MP4", "MOV", "MKV", "AVI", "WEBM", "WMV", "FLV", "GIF"},
    "document": DOCUMENT_FORMATS,
}


async def _login() -> str:
    async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{API_BASE_URL}{AUTH_LOGIN_PATH}",
            data={"username": BOT_API_USERNAME, "password": BOT_API_PASSWORD},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def _get_token() -> str:
    global _token
    async with _token_lock:
        if _token is None:
            _token = await _login()
    return _token


async def _invalidate_token() -> None:
    global _token
    async with _token_lock:
        _token = None


async def load_bot_token_from_db() -> str | None:
    """
    Load Telegram bot token from backend database (raw, unmasked).
    Falls back to TELEGRAM_BOT_TOKEN env var if DB fetch fails or token not set.
    Called at bot startup.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        resp = await _request("get", BOT_TOKEN_PATH, timeout=10)
        data = resp.json()
        token = data.get("telegram_bot_token")
        if token:
            logger.info("Bot token loaded from database.")
            return token
    except Exception as exc:
        logger.warning(f"Failed to load bot token from DB: {exc}. Falling back to env var.")

    # Fallback to environment variable
    return os.getenv("TELEGRAM_BOT_TOKEN")


async def _request(
    method: str,
    path: str,
    *,
    params: Optional[dict] = None,
    files: Optional[dict] = None,
    timeout: int = 300,
) -> httpx.Response:
    """Make an authenticated request, retrying once on 401."""
    for attempt in range(AUTH_RETRY_ATTEMPTS):
        token = await _get_token()
        headers = {"Authorization": f"Bearer {token}"}
        kwargs: dict = {"headers": headers}
        if params is not None:
            kwargs["params"] = params
        if files is not None:
            kwargs["files"] = files
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await getattr(client, method)(
                f"{API_BASE_URL}{path}",
                **kwargs,
            )
        if resp.status_code == 401 and attempt == 0:
            await _invalidate_token()
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError("Authentication failed after re-login attempt")


async def create_job(
    file_type: str,
    file_bytes: bytes,
    filename: str,
    target_format: str,
) -> dict:
    """Upload a file and create a conversion job. Returns the job response dict."""
    route = JOB_TYPE_ROUTES[file_type]
    params = {"target_format": target_format}
    files = {"file": (filename, file_bytes)}
    resp = await _request("post", f"/{route}/jobs", params=params, files=files)
    return resp.json()


async def get_job_status(job_id: str) -> dict:
    """Poll job status by job_id."""
    resp = await _request("get", f"/jobs/{job_id}", timeout=30)
    return resp.json()


async def download_job_result(file_type: str, job_id: str) -> tuple[bytes, str]:
    """
    Download the completed output file.
    Returns (file_bytes, output_filename).
    """
    route = JOB_TYPE_ROUTES[file_type]
    resp = await _request("get", f"/{route}/jobs/{job_id}/download", timeout=300)

    # Extract filename from Content-Disposition if present
    content_disposition = resp.headers.get("content-disposition", "")
    output_filename = DEFAULT_OUTPUT_FILENAME
    if "filename=" in content_disposition:
        output_filename = content_disposition.split("filename=")[-1].strip().strip('"')

    return resp.content, output_filename


async def poll_until_done(
    job_id: str,
    *,
    interval: float = DEFAULT_JOB_POLL_INTERVAL_SECONDS,
    max_wait: float = DEFAULT_JOB_POLL_MAX_WAIT_SECONDS,
) -> dict:
    """
    Poll job status until completed or failed.
    Raises TimeoutError if max_wait seconds elapse without resolution.
    """
    elapsed = 0.0
    while elapsed < max_wait:
        job = await get_job_status(job_id)
        status = job.get("status")
        if status == JOB_STATUS_COMPLETED:
            return job
        if status == JOB_STATUS_FAILED:
            raise RuntimeError(job.get("error_message") or "Job failed")
        await asyncio.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Job {job_id} did not complete within {max_wait}s")
