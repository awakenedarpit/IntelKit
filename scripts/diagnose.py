"""Diagnostic tool to find out why the Telegram bot is not responding."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import httpx

from app.config import load_settings


def main() -> int:
    print("=== IntelKit Stage 1 Diagnostics ===\n")

    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        print("[FAIL] .env file not found.")
        print("       Fix: Run `cp .env.example .env` and add your TELEGRAM_BOT_TOKEN.")
        return 1
    print("[OK]   .env file exists.")

    settings = load_settings()
    if not settings.is_bot_configured:
        print("[FAIL] TELEGRAM_BOT_TOKEN is missing or still a placeholder in .env.")
        print("       Fix: Paste your bot token from @BotFather after TELEGRAM_BOT_TOKEN=.")
        return 1
    print("[OK]   TELEGRAM_BOT_TOKEN is set.")

    api_base = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
    try:
        with httpx.Client(timeout=10.0) as client:
            me_resp = client.get(f"{api_base}/getMe").json()
            if not me_resp.get("ok"):
                print(f"[FAIL] Telegram rejected TELEGRAM_BOT_TOKEN: {me_resp.get('description')}")
                return 1
            bot_user = me_resp["result"].get("username", "unknown")
            print(f"[OK]   Telegram token is valid for @{bot_user}.")

            wh_resp = client.get(f"{api_base}/getWebhookInfo").json()
    except Exception as exc:
        print(f"[FAIL] Could not reach Telegram API: {type(exc).__name__}")
        return 1

    info = wh_resp.get("result", {})
    webhook_url = info.get("url") or ""
    pending = info.get("pending_update_count", 0)
    last_error = info.get("last_error_message") or ""

    if not webhook_url:
        print("[WARN] No Telegram webhook URL is currently registered.")
        print("       Option A (Webhook + ngrok): Start ngrok, set WEBHOOK_BASE_URL in .env,")
        print("                 then run `python scripts/set_webhook.py set`.")
        print("       Option B (No ngrok needed): Run `python scripts/run_polling.py`.")
    else:
        print(f"[INFO] Registered webhook URL: {webhook_url}")
        print(f"[INFO] Pending updates waiting in Telegram queue: {pending}")
        if last_error:
            print(f"[FAIL] Telegram's last delivery error: {last_error}")
            print("       Fix: Make sure ngrok and uvicorn are both running, and re-run")
            print("            `python scripts/set_webhook.py set` with your current ngrok URL.")

    local_health = f"http://127.0.0.1:{settings.port}/health"
    try:
        with httpx.Client(timeout=3.0) as client:
            health_resp = client.get(local_health)
            if health_resp.status_code == 200:
                print(f"[OK]   Local FastAPI server is running at {local_health}.")
            else:
                print(f"[WARN] Local server returned HTTP {health_resp.status_code} at {local_health}.")
    except Exception:
        print(f"[WARN] Local FastAPI server is NOT running at {local_health}.")
        print(f"       Start it with: uvicorn app.main:app --reload --port {settings.port}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
