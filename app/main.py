"""FastAPI entry point and Telegram webhook server for IntelKit Stage 1."""

from __future__ import annotations

import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status

from app.bot.client import create_telegram_application, process_telegram_update
from app.config import Settings, load_settings
from app.logging_config import setup_logging
from app.utils.deduplication import UpdateDeduplicator

logger = logging.getLogger("intelkit.main")


def _track_background_task(task_set: set[asyncio.Task[Any]], task: asyncio.Task[Any]) -> None:
    """Keep a strong reference to background tasks and log any uncaught failures."""
    task_set.add(task)

    def _on_done(completed: asyncio.Task[Any]) -> None:
        task_set.discard(completed)
        if completed.cancelled():
            return
        exc = completed.exception()
        if exc is not None:
            logger.error(
                "Background update task failed (%s): %s",
                type(exc).__name__,
                exc,
            )

    task.add_done_callback(_on_done)


def create_app(custom_settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = custom_settings or load_settings()
    setup_logging(log_level=settings.log_level, secrets=settings.known_secrets())

    @asynccontextmanager
    async def lifespan(fastapi_app: FastAPI):
        fastapi_app.state.settings = settings
        fastapi_app.state.deduplicator = UpdateDeduplicator(
            max_size=settings.max_dedup_cache_size
        )
        fastapi_app.state.background_tasks = set()
        fastapi_app.state.telegram_app = None

        if settings.is_bot_configured:
            telegram_app = create_telegram_application(settings)
            await telegram_app.initialize()
            await telegram_app.start()
            fastapi_app.state.telegram_app = telegram_app
            logger.info("IntelKit started in %s mode with Telegram bot active.", settings.app_env)
        else:
            logger.warning(
                "TELEGRAM_BOT_TOKEN is not set. FastAPI is running in limited mode; "
                "configure TELEGRAM_BOT_TOKEN in .env to enable Telegram webhook processing."
            )

        try:
            yield
        finally:
            telegram_app = getattr(fastapi_app.state, "telegram_app", None)
            if telegram_app is not None:
                await telegram_app.stop()
                await telegram_app.shutdown()
                logger.info("Telegram Application shut down cleanly.")

    fastapi_app = FastAPI(
        title="IntelKit",
        description="AI-Powered Content Intelligence Telegram Bot (Stage 1: Project Foundation)",
        version="0.1.0",
        lifespan=lifespan,
    )

    @fastapi_app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "service": "IntelKit",
            "stage": 1,
            "status": "running",
        }

    @fastapi_app.get("/health")
    async def health(request: Request) -> dict[str, Any]:
        app_settings: Settings = request.app.state.settings
        return {
            "status": "ok",
            "app": "intelkit",
            "stage": 1,
            "environment": app_settings.app_env,
            "bot_configured": app_settings.is_bot_configured,
        }

    @fastapi_app.post("/webhook/telegram")
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> dict[str, Any]:
        app_settings: Settings = request.app.state.settings

        if app_settings.telegram_webhook_secret:
            provided = x_telegram_bot_api_secret_token or ""
            if not hmac.compare_digest(provided, app_settings.telegram_webhook_secret):
                logger.warning("Rejected webhook request with invalid secret token.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid webhook secret token.",
                )

        telegram_app = getattr(request.app.state, "telegram_app", None)
        if telegram_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Telegram bot is not configured. Set TELEGRAM_BOT_TOKEN first.",
            )

        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            ) from exc

        if not isinstance(payload, dict) or not isinstance(payload.get("update_id"), int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram update payload must be a JSON object with an integer update_id.",
            )

        update_id: int = payload["update_id"]
        deduplicator: UpdateDeduplicator = request.app.state.deduplicator
        if deduplicator.is_duplicate(update_id):
            logger.info("Ignored duplicate Telegram update_id=%s", update_id)
            return {"ok": True, "status": "duplicate_ignored"}

        task = asyncio.create_task(process_telegram_update(telegram_app, payload))
        _track_background_task(request.app.state.background_tasks, task)
        logger.info("Accepted Telegram update_id=%s for background processing", update_id)
        return {"ok": True, "status": "accepted"}

    return fastapi_app


app = create_app()
