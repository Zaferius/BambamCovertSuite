"""
Handles incoming file messages from Telegram users.

Detects file type and shows appropriate conversion options via inline keyboard.
"""

from aiogram import Router, F
from aiogram.types import Message

from bot.services import file_detector, option_builder, session_store

router = Router()

# Match any message that carries a transferable file
_has_file = (
    F.photo
    | F.video
    | F.audio
    | F.voice
    | F.document
)


@router.message(_has_file)
async def handle_file(message: Message) -> None:
    detected = file_detector.detect(message)

    if detected is None:
        await message.answer("❌ Sorry, this file type is not supported.")
        return

    file_type, file_id, filename, mime_type = detected

    # Persist session for callback resolution
    session_store.set_session(
        message.from_user.id,
        session_store.Session(
            user_id=message.from_user.id,
            file_id=file_id,
            file_type=file_type,
            original_filename=filename,
            mime_type=mime_type,
        ),
    )

    keyboard = option_builder.build_keyboard(file_type)
    prompt = option_builder.describe_file(file_type)

    await message.answer(
        f"File received ✅ <b>{filename}</b>\n\n{prompt}",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
