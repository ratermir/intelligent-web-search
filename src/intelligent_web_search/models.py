from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class PublicStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    NOT_RETRIEVABLE = "not_retrievable"


class FetchMode(str, Enum):
    NONE = "none"
    SIMPLE = "simple"
    COMPLEX = "complex"


class InternalDecision(str, Enum):
    ACCEPT_SIMPLE = "accept_simple"
    RETRY_WITH_COMPLEX = "retry_with_complex"
    TERMINAL_FAIL = "terminal_fail"


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str = "ddgs"


class SearchResponse(BaseModel):
    query: str
    limit: int
    count: int
    results: list[SearchResult]


class RawFetchResult(BaseModel):
    url: str
    final_url: str | None = None
    fetch_mode: FetchMode
    ok: bool
    http_status: int | None = None
    title: str = ""
    html: str = ""
    text: str = ""
    markdown: str = ""
    error: str | None = None
    network_error: bool = False
    blocked: bool = False
    timed_out: bool = False
    content_type: str | None = None


class HeuristicSignals(BaseModel):
    text_length: int
    html_length: int
    has_cloudflare_marker: bool = False
    has_js_required_marker: bool = False
    has_spa_shell_marker: bool = False
    has_login_marker: bool = False
    has_captcha_marker: bool = False
    looks_like_error_page: bool = False
    has_useful_text: bool = False
    challenge_or_blocked: bool = False
    very_short_text: bool = False


class HeuristicDecision(BaseModel):
    decision: InternalDecision
    reason: str
    signals: HeuristicSignals


class FetchResponse(BaseModel):
    status: PublicStatus
    reason: str
    url: str
    final_url: str | None = None
    fetch_mode: FetchMode
    used_fallback: bool = False
    title: str = ""
    content: str = ""
    markdown: str = ""
    http_status: int | None = None
    diagnostics: dict[str, Any] | None = None


class RetrieveItem(BaseModel):
    search_result: SearchResult
    fetch: FetchResponse


class SmartRetrieveResponse(BaseModel):
    query: str
    search: SearchResponse
    items: list[RetrieveItem]


class FetchRequest(BaseModel):
    url: HttpUrl
    prefer_complex: bool = Field(default=False)
    debug: bool = Field(default=False)
