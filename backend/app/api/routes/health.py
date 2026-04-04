from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
