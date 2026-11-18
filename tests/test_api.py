"""FastAPI and Telegram webhook integration tests for Stage 1."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - allows bare stdlib unittest runs without pip deps
    FASTAPI_AVAILABLE = False


def _make_test_settings(*, token: str = "", secret: str = "") -> "Settings":
    return Settings(
        app_env="test",
        log_level="WARNING",
        port=8000,
        telegram_bot_token=token,
        telegram_webhook_secret=secret,
        webhook_base_url="",
        primary_provider="groq",
        fallback_providers=("gemini", "openrouter"),
        groq_api_key="",
        gemini_api_key="",
        openrouter_api_key="",
        max_dedup_cache_size=100,
    )


def _mock_telegram_app() -> MagicMock:
    mock_app = MagicMock()
    mock_app.bot = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.start = AsyncMock()
    mock_app.stop = AsyncMock()
    mock_app.shutdown = AsyncMock()
    mock_app.process_update = AsyncMock()
    return mock_app


@unittest.skipUnless(FASTAPI_AVAILABLE, "Install requirements.txt to run FastAPI integration tests")
class TestFastAPIEndpoints(unittest.TestCase):
    def test_health_endpoint_without_bot_token(self) -> None:
        app = create_app(_make_test_settings())
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["status"], "ok")
            self.assertEqual(body["stage"], 1)
            self.assertFalse(body["bot_configured"])

    def test_webhook_returns_503_when_bot_not_configured(self) -> None:
        app = create_app(_make_test_settings())
        with TestClient(app) as client:
            response = client.post("/webhook/telegram", json={"update_id": 1})
            self.assertEqual(response.status_code, 503)

    def test_webhook_rejects_invalid_secret_token(self) -> None:
        settings = _make_test_settings(token="123456:FAKE_TOKEN_FOR_TESTS", secret="top-secret")
        mock_tg = _mock_telegram_app()

        with patch("app.main.create_telegram_application", return_value=mock_tg):
            app = create_app(settings)
            with TestClient(app) as client:
                missing_resp = client.post("/webhook/telegram", json={"update_id": 10})
                self.assertEqual(missing_resp.status_code, 403)

                wrong_resp = client.post(
                    "/webhook/telegram",
                    json={"update_id": 10},
                    headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
                )
                self.assertEqual(wrong_resp.status_code, 403)

    def test_webhook_accepts_valid_update_and_ignores_duplicate(self) -> None:
        settings = _make_test_settings(token="123456:FAKE_TOKEN_FOR_TESTS", secret="top-secret")
        mock_tg = _mock_telegram_app()
        sample_update = {
            "update_id": 999001,
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 42, "type": "private"},
                "text": "/start",
            },
        }

        with (
            patch("app.main.create_telegram_application", return_value=mock_tg),
            patch("app.main.process_telegram_update", new=AsyncMock()) as mock_process,
        ):
            app = create_app(settings)
            with TestClient(app) as client:
                headers = {"X-Telegram-Bot-Api-Secret-Token": "top-secret"}

                first = client.post("/webhook/telegram", json=sample_update, headers=headers)
                self.assertEqual(first.status_code, 200)
                self.assertEqual(first.json()["status"], "accepted")

                second = client.post("/webhook/telegram", json=sample_update, headers=headers)
                self.assertEqual(second.status_code, 200)
                self.assertEqual(second.json()["status"], "duplicate_ignored")

                self.assertEqual(mock_process.await_count, 1)


if __name__ == "__main__":
    unittest.main()
