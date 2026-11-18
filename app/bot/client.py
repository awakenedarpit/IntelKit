"""Telegram Application initialization and update dispatch."""

from __future__ import annotations

import logging
from typing import Any

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.bot.handlers import (
    error_handler,
    handle_text_message,
    handle_unsupported_message,
    help_command,
    start_command,
)
from app.config import Settings

logger = logging.getLogger("intelkit.bot.client")


def create_telegram_application(
    settings: Settings,
    *,
    webhook_mode: bool = True,
) -> Application:
    """Create and configure a python-telegram-bot Application."""
    if not settings.is_bot_configured:
        raise ValueError("Cannot initialize Telegram Application without TELEGRAM_BOT_TOKEN.")

    builder = Application.builder().token(settings.telegram_bot_token)
    if webhook_mode:
        builder = builder.updater(None)
    application = builder.build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    application.add_handler(
        MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_unsupported_message)
    )
    application.add_error_handler(error_handler)

    logger.info("Telegram Application configured with Stage 1 handlers.")
    return application


async def process_telegram_update(application: Application, payload: dict[str, Any]) -> None:
    """Parse a raw Telegram webhook dictionary and pass it to python-telegram-bot."""
    update = Update.de_json(payload, application.bot)
    if update is None:
        logger.warning("Ignored empty or unparseable Telegram update payload.")
        return
    await application.process_update(update)
