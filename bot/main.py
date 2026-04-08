"""
Bambam Converter Bot — entry point.

Registers all handlers and starts aiogram long-polling.
Token is loaded from backend DB first; falls back to TELEGRAM_BOT_TOKEN env var.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.handlers import start, file_handler, callbacks
from bot.api import client as api_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Try loading token from backend database first; fall back to env var
    logger.info("Loading Telegram bot token...")
    token = await api_client.load_bot_token_from_db()

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not set in database or environment. "
            "Please configure it via the admin panel or set TELEGRAM_BOT_TOKEN env var."
        )

    logger.info("Token loaded. Initializing bot...")
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register routers — order matters: specific handlers before catch-all
    dp.include_router(start.router)
    dp.include_router(callbacks.router)
    dp.include_router(file_handler.router)

    logger.info("Starting Bambam Converter Bot...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
