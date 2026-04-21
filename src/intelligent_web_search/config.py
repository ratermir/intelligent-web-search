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

MAX_CONTENT_CHARS = getenv_int("IWS_MAX_CONTENT_CHARS", 120_000)
MIN_OK_TEXT_CHARS = getenv_int("IWS_MIN_OK_TEXT_CHARS", 500)
MIN_PARTIAL_TEXT_CHARS = getenv_int("IWS_MIN_PARTIAL_TEXT_CHARS", 120)

SIMPLE_FETCH_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_TIMEOUT", 12.0)
SIMPLE_FETCH_CONNECT_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_CONNECT_TIMEOUT", 5.0)
SIMPLE_FETCH_READ_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_READ_TIMEOUT", 10.0)
SIMPLE_FETCH_WRITE_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_WRITE_TIMEOUT", 10.0)
SIMPLE_FETCH_POOL_TIMEOUT = getenv_float("IWS_SIMPLE_FETCH_POOL_TIMEOUT", 5.0)
SIMPLE_FETCH_RETRIES = getenv_int("IWS_SIMPLE_FETCH_RETRIES", 1)
SIMPLE_FETCH_MAX_REDIRECTS = getenv_int("IWS_SIMPLE_FETCH_MAX_REDIRECTS", 8)

COMPLEX_FETCH_TIMEOUT = getenv_float("IWS_COMPLEX_FETCH_TIMEOUT", 25.0)
COMPLEX_FETCH_NAV_TIMEOUT = getenv_float("IWS_COMPLEX_FETCH_NAV_TIMEOUT", 18.0)
COMPLEX_FETCH_EXTRACT_TIMEOUT = getenv_float("IWS_COMPLEX_FETCH_EXTRACT_TIMEOUT", 6.0)
COMPLEX_FETCH_CONCURRENCY = getenv_int("IWS_COMPLEX_FETCH_CONCURRENCY", 2)
COMPLEX_FETCH_RETRIES = getenv_int("IWS_COMPLEX_FETCH_RETRIES", 0)
BROWSER_WAIT_UNTIL = os.getenv("IWS_BROWSER_WAIT_UNTIL", "domcontentloaded")
BROWSER_EXTRA_WAIT_MS = getenv_int("IWS_BROWSER_EXTRA_WAIT_MS", 1200)
BROWSER_ABORT_RESOURCE_TYPES = tuple(
    item.strip() for item in os.getenv("IWS_BROWSER_ABORT_RESOURCE_TYPES", "image,media,font").split(",") if item.strip()
)
HEADLESS = os.getenv("IWS_HEADLESS", "true").lower() not in {"0", "false", "no"}

DEBUG_INCLUDE_HTML_LENGTH = os.getenv("IWS_DEBUG_INCLUDE_HTML_LENGTH", "true").lower() not in {"0", "false", "no"}
