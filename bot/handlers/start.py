from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 Welcome to <b>Bambam Converter Bot</b>!\n\n"
        "Send me any file and I'll help you convert it.\n\n"
        "<b>Supported types:</b>\n"
        "🖼 Images → PNG, JPG, WEBP\n"
        "🎵 Audio → MP3, WAV\n"
        "🎬 Video → MP4\n"
        "📄 Documents → PDF",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📋 <b>How to use:</b>\n\n"
        "1. Send a file (photo, video, audio, or document)\n"
        "2. Choose a conversion option from the buttons\n"
        "3. Wait for processing ⏳\n"
        "4. Receive your converted file 🎉\n\n"
        "Send /start to see supported formats.",
        parse_mode="HTML",
    )
