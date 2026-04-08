"""Bot settings — singleton row for Telegram bot configuration."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    telegram_bot_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    bot_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
