"""Telegram command and message handlers for IntelKit Stage 1."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.utils.text_router import build_stage1_text_reply, classify_text_input

logger = logging.getLogger("intelkit.bot.handlers")


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    message = update.effective_message
    if message is None:
        return

    logger.info("Handled /start command for update_id=%s", update.update_id)
    await message.reply_text(
        "Welcome to IntelKit — Signal, not noise.\n\n"
        "IntelKit turns Instagram Reels, carousels, posts, images, and videos into "
        "concise, structured knowledge.\n\n"
        "Stage 1 (Foundation) is active:\n"
        "- /start — Show this introduction\n"
        "- /help — See supported inputs and roadmap\n"
        "- Send any text message or Instagram link to test input routing"
    )


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    message = update.effective_message
    if message is None:
        return

    logger.info("Handled /help command for update_id=%s", update.update_id)
    await message.reply_text(
        "IntelKit Help (Stage 1: Project Foundation)\n\n"
        "Currently active:\n"
        "- /start — Welcome message\n"
        "- /help — Usage guide\n"
        "- Plain text messages — Basic input validation & routing\n"
        "- Instagram links — Link type detection only\n\n"
        "Coming in upcoming stages:\n"
        "- Stage 2: AI Provider Manager (Groq, Gemini, OpenRouter)\n"
        "- Stage 3: Image OCR & visual intelligence\n"
        "- Stage 4: Carousel album intelligence\n"
        "- Stage 5: Video & audio transcription\n"
        "- Stage 6: Public Instagram URL retrieval\n"
        "- Stage 7: Full concise knowledge reports & verification"
    )


async def handle_text_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming non-command text messages."""
    message = update.effective_message
    if message is None:
        return

    classification = classify_text_input(message.text)
    logger.info(
        "Classified text update_id=%s as kind=%s",
        update.update_id,
        classification.kind.value,
    )
    reply = build_stage1_text_reply(classification)
    await message.reply_text(reply)


async def handle_unsupported_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-text uploads gracefully during Stage 1."""
    message = update.effective_message
    if message is None:
        return

    logger.info("Received non-text update_id=%s in Stage 1", update.update_id)
    await message.reply_text(
        "Media upload received, but image, album, and video processing are not enabled "
        "in Stage 1 yet.\n\n"
        "In Stage 1, please test /start, /help, or send a text message."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log handler errors safely without exposing secrets or private user data."""
    error_type = type(context.error).__name__ if context.error else "UnknownError"
    update_id = getattr(update, "update_id", None)
    logger.error(
        "Telegram handler error (%s) while processing update_id=%s",
        error_type,
        update_id,
    )

    if isinstance(update, Update) and update.effective_message is not None:
        try:
            await update.effective_message.reply_text(
                "Something went wrong while processing your message. Please try again."
            )
        except Exception:
            logger.warning("Failed to send fallback error reply for update_id=%s", update_id)
