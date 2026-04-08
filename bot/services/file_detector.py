"""
Detects the logical file type from a Telegram message.

Telegram may deliver images/videos as `document` messages.
Detection order: Telegram message type → MIME type → file extension.
"""

from pathlib import Path
from typing import Optional
from aiogram.types import Message

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".ico", ".svg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".gif", ".wmv", ".flv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"}


def _type_from_mime(mime: Optional[str]) -> Optional[str]:
    if not mime:
        return None
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    return None


def _type_from_extension(filename: str) -> Optional[str]:
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    return None


def detect(message: Message) -> Optional[tuple[str, str, str, Optional[str]]]:
    """
    Returns (file_type, file_id, original_filename, mime_type) or None if unsupported.
    """
    if message.photo:
        photo = message.photo[-1]  # largest size
        return "image", photo.file_id, "photo.jpg", "image/jpeg"

    if message.video:
        v = message.video
        filename = v.file_name or "video.mp4"
        return "video", v.file_id, filename, v.mime_type

    if message.audio:
        a = message.audio
        filename = a.file_name or "audio.mp3"
        return "audio", a.file_id, filename, a.mime_type

    if message.voice:
        return "audio", message.voice.file_id, "voice.ogg", "audio/ogg"

    if message.document:
        doc = message.document
        filename = doc.file_name or "file"
        mime = doc.mime_type

        # Try MIME first, then extension
        file_type = _type_from_mime(mime) or _type_from_extension(filename) or "document"
        return file_type, doc.file_id, filename, mime

    return None
