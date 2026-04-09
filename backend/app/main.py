import uuid
import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.constants import APP_DESCRIPTION, APP_VERSION
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.job import Job
from app.models.user import User
from app.models.bot_settings import BotSettings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


from sqlalchemy import text

@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        try:
            db.execute(text("ALTER TABLE jobs ADD COLUMN user_id VARCHAR(36)"))
            db.commit()
        except Exception:
            db.rollback()

        # Add user_id column to bot_settings if it doesn't exist
        try:
            db.execute(text("ALTER TABLE bot_settings ADD COLUMN user_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        if db.query(User).count() == 0:
            admin_user = User(
                id=uuid.uuid4().hex,
                username=settings.admin_username,
                hashed_password=get_password_hash(settings.admin_password),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

    # Auto-scale workers to the configured default on startup.
    # Runs in a background thread so it doesn't block the API from accepting
    # requests while docker compose is doing its thing.
    if settings.worker_scale_enabled:
        def _auto_scale() -> None:
            # Brief delay so Redis and the compose daemon are ready before we issue
            # the scale command.
            time.sleep(8)
            try:
                from app.api.routes.admin import _run_compose_scale
                from app.worker import set_worker_target_count
                target = settings.worker_target_default
                code, _ = _run_compose_scale(target)
                if code == 0:
                    set_worker_target_count(target)
            except Exception:
                pass

        threading.Thread(target=_auto_scale, daemon=True).start()
