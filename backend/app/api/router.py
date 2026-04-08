from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.audio import router as audio_router
from app.api.routes.document import router as document_router
from app.api.routes.health import router as health_router
from app.api.routes.image import router as image_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.root import router as root_router
from app.api.routes.video import router as video_router
from app.api.routes.auth import router as auth_router
from app.api.routes.batch import router as batch_router

api_router = APIRouter()

api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(batch_router)
api_router.include_router(image_router)
api_router.include_router(audio_router)
api_router.include_router(document_router)
api_router.include_router(jobs_router)
api_router.include_router(video_router)
