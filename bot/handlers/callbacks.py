"""
Handles inline keyboard callback queries.

Flow:
  1. Parse action from callback data
  2. Retrieve session (file_id, file_type)
  3. Download file from Telegram
  4. Submit job to backend
  5. Poll until done
  6. Send result to user
"""

import io
import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, BufferedInputFile

from bot.api import client as api
from bot.services import session_store

logger = logging.getLogger(__name__)
router = Router()

# Callback data pattern: "action:{action_name}"  e.g. "action:conv_MP3"
_ACTION_PREFIX = "action:"


@router.callback_query(F.data.startswith(_ACTION_PREFIX))
async def handle_action(callback: CallbackQuery, bot: Bot) -> None:
    action = callback.data[len(_ACTION_PREFIX):]  # e.g. "conv_MP3"
    user_id = callback.from_user.id

    session = session_store.get_session(user_id)
    if session is None:
        await callback.answer("Session expired. Please send the file again.", show_alert=True)
        return

    await callback.answer()  # dismiss loading indicator on the button

    # Parse target_format from action string (format: "conv_{FORMAT}")
    if not action.startswith("conv_"):
        await callback.message.answer("❌ Unknown action.")
        return

    target_format = action[len("conv_"):]  # e.g. "MP3"

    status_msg = await callback.message.answer("Processing... ⏳")

    try:
        # --- Download file from Telegram ---
        file_info = await bot.get_file(session.file_id)
        file_bytes_io = await bot.download_file(file_info.file_path)
        file_bytes = file_bytes_io.read()

        # --- Submit job to backend ---
        job_response = await api.create_job(
            file_type=session.file_type,
            file_bytes=file_bytes,
            filename=session.original_filename,
            target_format=target_format,
        )
        job_id = job_response["job_id"]
        session.job_id = job_id
        session.selected_action = action

        # --- Poll until done ---
        await api.poll_until_done(job_id)

        # --- Download result ---
        result_bytes, output_filename = await api.download_job_result(
            session.file_type, job_id
        )

        # --- Send result to user ---
        await callback.message.answer_document(
            document=BufferedInputFile(result_bytes, filename=output_filename),
            caption="Completed 🎉",
        )

    except TimeoutError:
        logger.warning("Job timed out for user %s", user_id)
        await callback.message.answer("Failed ❌ — job timed out. Please try again.")
    except RuntimeError as exc:
        logger.error("Job failed for user %s: %s", user_id, exc)
        await callback.message.answer(f"Failed ❌ — {exc}")
    except Exception as exc:
        logger.exception("Unexpected error for user %s", user_id)
        await callback.message.answer("Failed ❌ — an unexpected error occurred.")
    finally:
        # Clean up session and status message
        session_store.clear_session(user_id)
        try:
            await status_msg.delete()
        except Exception:
            pass
