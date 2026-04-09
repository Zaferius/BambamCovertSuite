"""
Builds inline keyboard options based on detected file type.

Callback data format: "action:{action_name}"
This keeps the structure extensible for future AI-driven intent layers.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Maps file_type → list of (label, action_name)
OPERATIONS: dict[str, list[tuple[str, str]]] = {
    "image": [
        ("Convert to PNG", "conv_PNG"),
        ("Convert to JPG", "conv_JPG"),
        ("Convert to WEBP", "conv_WEBP"),
        ("Convert to ICO", "conv_ICO"),
    ],
    "audio": [
        ("Convert to MP3", "conv_MP3"),
        ("Convert to WAV", "conv_WAV"),
        ("Convert to FLAC", "conv_FLAC"),
        ("Convert to OGG", "conv_OGG"),
        ("Convert to M4A", "conv_M4A"),
        ("Convert to AAC", "conv_AAC"),
        ("Convert to WMA", "conv_WMA"),
        ("Convert to OPUS", "conv_OPUS"),
        ("Convert to AIFF", "conv_AIFF"),
    ],
    "video": [
        ("Convert to MP4", "conv_MP4"),
        ("Convert to MOV", "conv_MOV"),
        ("Convert to MKV", "conv_MKV"),
        ("Convert to AVI", "conv_AVI"),
        ("Convert to WEBM", "conv_WEBM"),
        ("Convert to WMV", "conv_WMV"),
        ("Convert to FLV", "conv_FLV"),
        ("Convert to GIF", "conv_GIF"),
    ],
    "document": [
        ("Convert to PDF", "conv_PDF"),
    ],
}

TYPE_LABELS = {
    "image": "image",
    "audio": "audio",
    "video": "video",
    "document": "document",
}


def build_keyboard(file_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, action in OPERATIONS.get(file_type, []):
        builder.button(text=label, callback_data=f"action:{action}")
    builder.adjust(1)
    return builder.as_markup()


def describe_file(file_type: str) -> str:
    label = TYPE_LABELS.get(file_type, "file")
    return f"This is a {label} file. What would you like to do?"
