"""
In-memory session store keyed by Telegram user_id.
Holds temporary state between file receipt and action selection.

Future: replace with Redis for multi-instance deployments.
"""

from dataclasses import dataclass, field
from typing import Optional

_sessions: dict[int, "Session"] = {}


@dataclass
class Session:
    user_id: int
    file_id: str
    file_type: str          # "image" | "audio" | "video" | "document"
    original_filename: str
    mime_type: Optional[str] = None
    job_id: Optional[str] = None
    selected_action: Optional[str] = None


def set_session(user_id: int, session: Session) -> None:
    _sessions[user_id] = session


def get_session(user_id: int) -> Optional[Session]:
    return _sessions.get(user_id)


def clear_session(user_id: int) -> None:
    _sessions.pop(user_id, None)
