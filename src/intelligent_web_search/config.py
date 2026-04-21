from __future__ import annotations

import os


def getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def getenv_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


USER_AGENT = os.getenv(
    "IWS_USER_AGENT",
    "IntelligentWebSearch/0.1 (+https://localhost; self-hosted retrieval service)",
)
SIMPLE_FETCH_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_TIMEOUT", 12.0)
COMPLEX_FETCH_TIMEOUT = getenv_float("IWS_COMPLEX_FETCH_TIMEOUT", 25.0)
COMPLEX_FETCH_CONCURRENCY = getenv_int("IWS_COMPLEX_FETCH_CONCURRENCY", 2)
MAX_CONTENT_CHARS = getenv_int("IWS_MAX_CONTENT_CHARS", 120_000)
MIN_OK_TEXT_CHARS = getenv_int("IWS_MIN_OK_TEXT_CHARS", 500)
MIN_PARTIAL_TEXT_CHARS = getenv_int("IWS_MIN_PARTIAL_TEXT_CHARS", 120)
BROWSER_WAIT_UNTIL = os.getenv("IWS_BROWSER_WAIT_UNTIL", "domcontentloaded")
BROWSER_EXTRA_WAIT_MS = getenv_int("IWS_BROWSER_EXTRA_WAIT_MS", 1200)
HEADLESS = os.getenv("IWS_HEADLESS", "true").lower() not in {"0", "false", "no"}
