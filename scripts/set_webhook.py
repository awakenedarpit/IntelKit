"""Beginner-friendly helper script to register or inspect your Telegram webhook."""

from __future__ import annotations

import argparse
import sys

import httpx

from app.config import load_settings


def register_webhook(webhook_base_url: str, *, drop_pending: bool = False) -> int:
    """Register <webhook_base_url>/webhook/telegram with the Telegram Bot API."""
    settings = load_settings()
    if not settings.is_bot_configured:
        print("Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        return 1

    base = webhook_base_url.strip().rstrip("/")
    if not base.startswith("https://"):
        print("Error: Telegram requires an HTTPS webhook URL (e.g., https://xxxx.ngrok-free.app).")
        return 1

    webhook_url = f"{base}/webhook/telegram"
    api_base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"

    payload: dict[str, object] = {
        "url": webhook_url,
        "drop_pending_updates": drop_pending,
    }
    if settings.telegram_webhook_secret:
        payload["secret_token"] = settings.telegram_webhook_secret

    with httpx.Client(timeout=15.0) as client:
        response = client.post(f"{api_base}/setWebhook", json=payload)
        data = response.json()

    if response.status_code != 200 or not data.get("ok"):
        description = data.get("description", "Unknown error")
        print(f"Failed to register webhook: {description}")
        return 1

    print(f"Success: Telegram webhook registered to {webhook_url}")
    return 0


def check_webhook() -> int:
    """Print current Telegram webhook status without exposing the bot token."""
    settings = load_settings()
    if not settings.is_bot_configured:
        print("Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        return 1

    api_base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    with httpx.Client(timeout=15.0) as client:
        response = client.get(f"{api_base}/getWebhookInfo")
        data = response.json()

    if response.status_code != 200 or not data.get("ok"):
        print("Failed to fetch webhook info.")
        return 1

    info = data.get("result", {})
    print("Current Telegram Webhook Info:")
    print(f"  URL: {info.get('url') or '(not set)'}")
    print(f"  Pending updates: {info.get('pending_update_count', 0)}")
    if info.get("last_error_message"):
        print(f"  Last error: {info.get('last_error_message')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage IntelKit Telegram webhook.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_parser = subparsers.add_parser("set", help="Register the Telegram webhook URL")
    set_parser.add_argument(
        "--url",
        default="",
        help="Public HTTPS base URL (defaults to WEBHOOK_BASE_URL from .env)",
    )
    set_parser.add_argument(
        "--drop-pending",
        action="store_true",
        help="Discard queued updates sent while the bot was offline",
    )

    subparsers.add_parser("info", help="Check current Telegram webhook configuration")

    args = parser.parse_args()
    if args.command == "info":
        return check_webhook()

    settings = load_settings()
    target_url = args.url or settings.webhook_base_url
    if not target_url:
        print("Error: Provide --url https://... or set WEBHOOK_BASE_URL in .env.")
        return 1

    return register_webhook(target_url, drop_pending=args.drop_pending)


if __name__ == "__main__":
    sys.exit(main())
