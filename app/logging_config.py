"""Safe application logging with automatic secret redaction."""

from __future__ import annotations

import logging
import re
import sys
from typing import Iterable


_TOKEN_PATTERNS = (
    # Telegram Bot API URLs look like https://api.telegram.org/bot123456:ABC.../getMe
    re.compile(r"bot\d+:[A-Za-z0-9_-]{10,}"),
    # Common provider key prefixes
    re.compile(r"\bgsk_[A-Za-z0-9]{10,}\b"),
    re.compile(r"\bsk-or-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{16,}\b"),
)


def redact_secrets(text: str, secrets: Iterable[str] = ()) -> str:
    """Replace known secret values and token patterns with [REDACTED]."""
    if not text:
        return text

    sanitized = text
    for secret in secrets:
        if secret and secret in sanitized:
            sanitized = sanitized.replace(secret, "[REDACTED]")

    for pattern in _TOKEN_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)

    return sanitized


class SecretRedactingFilter(logging.Filter):
    """Logging filter that scrubs secrets from log messages and formatted args."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        super().__init__()
        self._secrets = tuple(s for s in secrets if s)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            rendered = record.getMessage()
        except Exception:
            rendered = str(record.msg)

        record.msg = redact_secrets(rendered, self._secrets)
        record.args = ()
        return True


def setup_logging(log_level: str = "INFO", secrets: Iterable[str] = ()) -> logging.Logger:
    """Configure root logging with secret redaction and return the intelkit logger."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers so repeated initialization in tests does not duplicate lines.
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    handler.addFilter(SecretRedactingFilter(secrets))
    root_logger.addHandler(handler)

    # Prevent verbose third-party HTTP debug logs from cluttering output or exposing URLs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logging.getLogger("intelkit")
