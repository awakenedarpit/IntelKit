"""Pure text input validation and Stage 1 routing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class InputKind(str, Enum):
    """Supported Stage 1 text classification categories."""

    EMPTY = "empty"
    TOO_LONG = "too_long"
    INSTAGRAM_URL = "instagram_url"
    OTHER_URL = "other_url"
    PLAIN_TEXT = "plain_text"


@dataclass(frozen=True)
class TextClassification:
    """Result of inspecting an incoming text message."""

    kind: InputKind
    cleaned_text: str
    detected_url: str | None = None
    instagram_content_type: str | None = None


_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_INSTAGRAM_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "m.instagram.com",
    "instagr.am",
    "www.instagr.am",
}


def _detect_instagram_content_type(path: str) -> str:
    normalized = path.lower().strip("/")
    if normalized.startswith(("reel/", "reels/")):
        return "reel"
    if normalized.startswith("p/"):
        return "post_or_carousel"
    if normalized.startswith("tv/"):
        return "video"
    return "link"


def classify_text_input(raw_text: str | None, max_length: int = 4000) -> TextClassification:
    """Validate and classify a Telegram text message without network calls."""
    cleaned = (raw_text or "").strip()
    if not cleaned:
        return TextClassification(kind=InputKind.EMPTY, cleaned_text="")

    if len(cleaned) > max_length:
        return TextClassification(kind=InputKind.TOO_LONG, cleaned_text=cleaned[:max_length])

    match = _URL_PATTERN.search(cleaned)
    if match:
        url = match.group(0).rstrip(".,);!?")
        parsed = urlparse(url)
        host = parsed.netloc.lower().split(":")[0]
        if host in _INSTAGRAM_HOSTS:
            return TextClassification(
                kind=InputKind.INSTAGRAM_URL,
                cleaned_text=cleaned,
                detected_url=url,
                instagram_content_type=_detect_instagram_content_type(parsed.path),
            )
        return TextClassification(
            kind=InputKind.OTHER_URL,
            cleaned_text=cleaned,
            detected_url=url,
        )

    return TextClassification(kind=InputKind.PLAIN_TEXT, cleaned_text=cleaned)


def build_stage1_text_reply(classification: TextClassification) -> str:
    """Generate a concise, honest Stage 1 response for classified text input."""
    if classification.kind == InputKind.EMPTY:
        return "Please send a non-empty text message, or use /help to see what works right now."

    if classification.kind == InputKind.TOO_LONG:
        return (
            "Your message is too long for Stage 1 testing (maximum 4,000 characters). "
            "Please send a shorter message."
        )

    if classification.kind == InputKind.INSTAGRAM_URL:
        content_label = (classification.instagram_content_type or "link").replace("_", " ")
        return (
            f"Instagram {content_label} link detected.\n\n"
            "Stage 1 status: Bot connection and input detection are working.\n"
            "Instagram retrieval and AI extraction will be added in later stages "
            "(Stages 2 and 6)."
        )

    if classification.kind == InputKind.OTHER_URL:
        return (
            "Link received, but external web scraping is not part of IntelKit Stage 1.\n\n"
            "Use /help to see supported commands and upcoming stages."
        )

    word_count = len(classification.cleaned_text.split())
    char_count = len(classification.cleaned_text)
    return (
        f"Text received ({word_count} words, {char_count} characters).\n\n"
        "Stage 1 status: FastAPI webhook and Telegram message handling are working.\n"
        "AI knowledge extraction will be connected in Stage 2."
    )
