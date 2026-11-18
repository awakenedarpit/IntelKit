"""Optional local-only polling runner so you can test the bot without ngrok.

Note: In production on Render, IntelKit uses the FastAPI webhook server (app/main.py).
Use this script only for quick local testing on your own computer if you do not have
ngrok or a public HTTPS URL running.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import httpx

from app.bot.client import create_telegram_application
from app.config import load_settings
from app.logging_config import setup_logging


def main() -> int:
    settings = load_settings()
    setup_logging(log_level=settings.log_level, secrets=settings.known_secrets())
    logger = logging.getLogger("intelkit.polling")

    if not settings.is_bot_configured:
        print("Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        return 1

    # Polling cannot run while a webhook is still registered on Telegram.
    api_base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(f"{api_base}/deleteWebhook", json={"drop_pending_updates": False})
        if resp.status_code != 200 or not resp.json().get("ok"):
            print("Warning: Could not clear previous webhook automatically.")

    application = create_telegram_application(settings, webhook_mode=False)
    logger.info("Starting local polling mode. Press Ctrl+C to stop.")
    application.run_polling(drop_pending_updates=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
