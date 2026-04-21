from __future__ import annotations

import re

from .config import MIN_OK_TEXT_CHARS, MIN_PARTIAL_TEXT_CHARS
from .models import HeuristicDecision, HeuristicSignals, InternalDecision, RawFetchResult


MARKERS = {
    "cloudflare": [
        "checking your browser",
        "just a moment",
        "cf-chl",
        "cloudflare",
        "attention required",
    ],
    "js_required": [
        "enable javascript",
        "javascript is required",
        "please enable javascript",
    ],
    "spa_shell": [
        'id="app"',
        'id="root"',
        "__next_data__",
        "__nuxt__",
        "window.__initial_state__",
        "hydration",
        "loading...",
    ],
    "login": [
        "sign in",
        "log in",
        "single sign-on",
        "authentication required",
    ],
    "captcha": [
        "captcha",
        "verify you are human",
        "robot check",
    ],
    "error_page": [
        "access denied",
        "request blocked",
        "service unavailable",
        "error 403",
        "error 429",
    ],
}


TAG_RE = re.compile(r"<[^>]+>")


def _contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in patterns)


def analyze(fetch: RawFetchResult) -> HeuristicDecision:
    html = fetch.html or ""
    text = fetch.text or ""
    combined = f"{html}\n{text}".lower()

    text_length = len(text)
    html_length = len(html)

    signals = HeuristicSignals(
        text_length=text_length,
        html_length=html_length,
        has_cloudflare_marker=_contains_any(combined, MARKERS["cloudflare"]),
        has_js_required_marker=_contains_any(combined, MARKERS["js_required"]),
        has_spa_shell_marker=_contains_any(combined, MARKERS["spa_shell"]),
        has_login_marker=_contains_any(combined, MARKERS["login"]),
        has_captcha_marker=_contains_any(combined, MARKERS["captcha"]),
        looks_like_error_page=_contains_any(combined, MARKERS["error_page"]),
        has_useful_text=text_length >= MIN_OK_TEXT_CHARS,
        challenge_or_blocked=fetch.blocked,
        very_short_text=text_length < MIN_PARTIAL_TEXT_CHARS,
    )

    if fetch.network_error or fetch.timed_out:
        return HeuristicDecision(
            decision=InternalDecision.TERMINAL_FAIL,
            reason=fetch.error or "network_or_timeout",
            signals=signals,
        )

    if fetch.http_status in {404, 410}:
        return HeuristicDecision(
            decision=InternalDecision.TERMINAL_FAIL,
            reason="not_found",
            signals=signals,
        )

    if fetch.http_status in {401, 403, 429}:
        return HeuristicDecision(
            decision=InternalDecision.RETRY_WITH_COMPLEX,
            reason="blocked_or_challenge_http_status",
            signals=signals,
        )

    if signals.has_cloudflare_marker or signals.has_captcha_marker:
        return HeuristicDecision(
            decision=InternalDecision.RETRY_WITH_COMPLEX,
            reason="challenge_or_bot_protection_detected",
            signals=signals,
        )

    if signals.has_js_required_marker:
        return HeuristicDecision(
            decision=InternalDecision.RETRY_WITH_COMPLEX,
            reason="javascript_required_marker_detected",
            signals=signals,
        )

    if signals.has_spa_shell_marker and text_length < MIN_OK_TEXT_CHARS:
        return HeuristicDecision(
            decision=InternalDecision.RETRY_WITH_COMPLEX,
            reason="spa_shell_marker_with_insufficient_text",
            signals=signals,
        )

    if not fetch.ok and fetch.http_status and fetch.http_status >= 500:
        return HeuristicDecision(
            decision=InternalDecision.TERMINAL_FAIL,
            reason=f"upstream_http_{fetch.http_status}",
            signals=signals,
        )

    if text_length >= MIN_OK_TEXT_CHARS:
        return HeuristicDecision(
            decision=InternalDecision.ACCEPT_SIMPLE,
            reason="sufficient_text_detected",
            signals=signals,
        )

    if text_length >= MIN_PARTIAL_TEXT_CHARS and not (
        signals.has_spa_shell_marker
        or signals.has_js_required_marker
        or signals.has_cloudflare_marker
        or signals.has_captcha_marker
    ):
        return HeuristicDecision(
            decision=InternalDecision.ACCEPT_SIMPLE,
            reason="partial_but_usable_text_detected",
            signals=signals,
        )

    return HeuristicDecision(
        decision=InternalDecision.RETRY_WITH_COMPLEX,
        reason="insufficient_text_or_uncertain_result",
        signals=signals,
    )
