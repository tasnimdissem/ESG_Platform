from __future__ import annotations

import io
import os
import re
from typing import Any

from openai import OpenAI

SUPPORTED_LANGUAGES: dict[str, str | None] = {
    "auto": None,
    "en": "en",
    "fr": "fr",
    "es": "es",
    "de": "de",
    "ar": "ar",
    "zh": "zh",
    "pt": "pt",
    "it": "it",
    "nl": "nl",
    "ja": "ja",
    "ko": "ko",
}

ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "webm", "ogg", "flac", "mpga", "mpeg", "mp4"}

_COMMAND_PATTERNS: list[tuple[str, str]] = [
    (r"^(search for|find|look for|cherche|trouve)\s+(.+)", "search"),
    (r"^(compare|comparer|versus|vs)\s+(.+)", "compare"),
    (r"^(top|best|worst|rank|liste|classement)\s+(.+)", "rank"),
    (r"^(what is|tell me about|explain|what are|quoi|c.est quoi|explique)\s+(.+)", "ask"),
]


def transcribe_audio(audio_bytes: bytes, filename: str, language: str | None = None) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured for transcription")

    client = OpenAI(api_key=api_key)
    buf = io.BytesIO(audio_bytes)

    kwargs: dict[str, Any] = {
        "model": "whisper-1",
        "file": (filename, buf),
        "response_format": "text",
    }
    if language and language != "auto":
        kwargs["language"] = language

    result = client.audio.transcriptions.create(**kwargs)
    return (str(result) if isinstance(result, str) else "").strip()


def detect_command(text: str) -> dict[str, str]:
    normalized = text.strip()
    for pattern, cmd_type in _COMMAND_PATTERNS:
        m = re.match(pattern, normalized, re.IGNORECASE)
        if m:
            query = normalized[m.end(1):].strip() or text
            return {"command": cmd_type, "query": query}
    return {"command": "ask", "query": text}


def resolve_language(lang_param: str | None) -> str | None:
    if not lang_param:
        return None
    key = lang_param.strip().lower()
    return SUPPORTED_LANGUAGES.get(key, None)
