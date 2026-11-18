"""Unit tests for Stage 1 core modules (configuration, logging, deduplication, routing)."""

from __future__ import annotations

import logging
import os
import unittest
from unittest.mock import patch

from app.config import load_settings
from app.logging_config import SecretRedactingFilter, redact_secrets
from app.utils.deduplication import UpdateDeduplicator
from app.utils.text_router import InputKind, build_stage1_text_reply, classify_text_input


class TestConfig(unittest.TestCase):
    def test_defaults_when_env_empty(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_settings(load_env_file=False)
            self.assertEqual(settings.app_env, "development")
            self.assertEqual(settings.log_level, "INFO")
            self.assertEqual(settings.port, 8000)
            self.assertEqual(settings.primary_provider, "groq")
            self.assertEqual(settings.fallback_providers, ("gemini", "openrouter"))
            self.assertFalse(settings.is_bot_configured)

    def test_placeholder_token_is_not_treated_as_configured(self) -> None:
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN"}, clear=True):
            settings = load_settings(load_env_file=False)
            self.assertFalse(settings.is_bot_configured)

    def test_invalid_port_raises_value_error(self) -> None:
        with patch.dict(os.environ, {"PORT": "not-a-number"}, clear=True):
            with self.assertRaises(ValueError):
                load_settings(load_env_file=False)


class TestLoggingRedaction(unittest.TestCase):
    def test_redact_explicit_secrets_and_telegram_urls(self) -> None:
        sample = (
            "Calling https://api.telegram.org/bot123456789:ABCDEFghijkLMNOPqrstUV/getMe "
            "with key gsk_supersecretkey12345"
        )
        redacted = redact_secrets(sample, secrets=("my_webhook_secret_value",))
        self.assertNotIn("123456789:ABCDEF", redacted)
        self.assertNotIn("gsk_supersecretkey12345", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_log_filter_scrubs_formatted_args(self) -> None:
        secret = "secret-token-value-12345"
        log_filter = SecretRedactingFilter(secrets=(secret,))
        record = logging.LogRecord(
            name="intelkit.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Header token=%s",
            args=(secret,),
            exc_info=None,
        )
        self.assertTrue(log_filter.filter(record))
        self.assertNotIn(secret, record.getMessage())
        self.assertIn("[REDACTED]", record.getMessage())


class TestDeduplication(unittest.TestCase):
    def test_duplicate_update_detection_and_eviction(self) -> None:
        dedup = UpdateDeduplicator(max_size=2)
        self.assertFalse(dedup.is_duplicate(101))
        self.assertTrue(dedup.is_duplicate(101))
        self.assertFalse(dedup.is_duplicate(102))
        self.assertFalse(dedup.is_duplicate(103))
        # 101 was the oldest entry when 103 arrived, so 101 was evicted and 102 remains cached.
        self.assertTrue(dedup.is_duplicate(102))
        self.assertFalse(dedup.is_duplicate(101))


class TestTextRouter(unittest.TestCase):
    def test_classify_empty_and_too_long(self) -> None:
        self.assertEqual(classify_text_input("   ").kind, InputKind.EMPTY)
        self.assertEqual(classify_text_input("a" * 50, max_length=10).kind, InputKind.TOO_LONG)

    def test_classify_instagram_reel_and_post_urls(self) -> None:
        reel = classify_text_input("Check this https://www.instagram.com/reel/ABC123xyz/")
        self.assertEqual(reel.kind, InputKind.INSTAGRAM_URL)
        self.assertEqual(reel.instagram_content_type, "reel")

        post = classify_text_input("https://instagram.com/p/XYZ987/")
        self.assertEqual(post.kind, InputKind.INSTAGRAM_URL)
        self.assertEqual(post.instagram_content_type, "post_or_carousel")

    def test_classify_other_url_and_plain_text(self) -> None:
        other = classify_text_input("Read https://example.com/article")
        self.assertEqual(other.kind, InputKind.OTHER_URL)

        plain = classify_text_input("Remember to review Python FastAPI basics.")
        self.assertEqual(plain.kind, InputKind.PLAIN_TEXT)
        reply = build_stage1_text_reply(plain)
        self.assertIn("6 words", reply)
        self.assertIn("Stage 1", reply)


if __name__ == "__main__":
    unittest.main()
