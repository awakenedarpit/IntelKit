"""Environment configuration loader for IntelKit."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in bare stdlib test runs
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class Settings:
    """Validated runtime settings loaded from environment variables."""

    app_env: str
    log_level: str
    port: int
    telegram_bot_token: str
    telegram_webhook_secret: str
    webhook_base_url: str
    primary_provider: str
    fallback_providers: tuple[str, ...]
    groq_api_key: str
    gemini_api_key: str
    openrouter_api_key: str
    max_dedup_cache_size: int = 1000

    @property
    def is_bot_configured(self) -> bool:
        """Return True when a real-looking Telegram bot token is present."""
        token = self.telegram_bot_token.strip()
        if not token:
            return False
        placeholder_prefixes = ("YOUR_", "REPLACE_", "EXAMPLE_")
        return not token.upper().startswith(placeholder_prefixes)

    def known_secrets(self) -> tuple[str, ...]:
        """Return non-empty secret strings that must never appear in logs."""
        candidates = (
            self.telegram_bot_token,
            self.telegram_webhook_secret,
            self.groq_api_key,
            self.gemini_api_key,
            self.openrouter_api_key,
        )
        return tuple(value for value in candidates if value and len(value.strip()) >= 6)


def _parse_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}.") from exc
    if value < minimum:
        raise ValueError(f"Environment variable {name} must be >= {minimum}, got {value}.")
    return value


def _parse_csv(raw: str) -> tuple[str, ...]:
    items = [item.strip().lower() for item in raw.split(",") if item.strip()]
    return tuple(items)


def load_settings(*, load_env_file: bool = True) -> Settings:
    """Load settings from .env (optional) and process environment variables."""
    if load_env_file:
        load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    if log_level not in _VALID_LOG_LEVELS:
        log_level = "INFO"

    port = _parse_int("PORT", default=8000, minimum=1)
    max_dedup = _parse_int("MAX_DEDUP_CACHE_SIZE", default=1000, minimum=10)

    fallback_raw = os.getenv("FALLBACK_PROVIDERS", "gemini,openrouter")
    fallback_providers = _parse_csv(fallback_raw) or ("gemini", "openrouter")

    return Settings(
        app_env=os.getenv("APP_ENV", "development").strip() or "development",
        log_level=log_level,
        port=port,
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip(),
        webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/"),
        primary_provider=os.getenv("PRIMARY_PROVIDER", "groq").strip().lower() or "groq",
        fallback_providers=fallback_providers,
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        max_dedup_cache_size=max_dedup,
    )
