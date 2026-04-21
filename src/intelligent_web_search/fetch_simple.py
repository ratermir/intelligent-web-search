from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import (
    SIMPLE_FETCH_CONNECT_TIMEOUT,
    SIMPLE_FETCH_MAX_REDIRECTS,
    SIMPLE_FETCH_POOL_TIMEOUT,
    SIMPLE_FETCH_READ_TIMEOUT,
    SIMPLE_FETCH_RETRIES,
    SIMPLE_FETCH_TIMEOUT,
    SIMPLE_FETCH_WRITE_TIMEOUT,
    USER_AGENT,
)
from .extract import html_title, html_to_text_and_markdown
from .models import FetchMode, RawFetchResult


class SimpleFetcher:
    def __init__(self) -> None:
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        }
        self._timeout = httpx.Timeout(
            timeout=SIMPLE_FETCH_TIMEOUT,
            connect=SIMPLE_FETCH_CONNECT_TIMEOUT,
            read=SIMPLE_FETCH_READ_TIMEOUT,
            write=SIMPLE_FETCH_WRITE_TIMEOUT,
            pool=SIMPLE_FETCH_POOL_TIMEOUT,
        )

    def _client(self) -> httpx.Client:
        return httpx.Client(
            headers=self._headers,
            follow_redirects=True,
            timeout=self._timeout,
            http2=True,
            max_redirects=SIMPLE_FETCH_MAX_REDIRECTS,
        )

    def fetch(self, url: str) -> RawFetchResult:
        try:
            response = self._request_with_retry(url)
        except httpx.TimeoutException:
            return RawFetchResult(
                url=url,
                fetch_mode=FetchMode.SIMPLE,
                ok=False,
                error="simple_fetch_timeout",
                timed_out=True,
                network_error=True,
            )
        except httpx.TooManyRedirects:
            return RawFetchResult(
                url=url,
                fetch_mode=FetchMode.SIMPLE,
                ok=False,
                error="simple_fetch_too_many_redirects",
                network_error=True,
            )
        except httpx.HTTPError as exc:
            return RawFetchResult(
                url=url,
                fetch_mode=FetchMode.SIMPLE,
                ok=False,
                error=f"simple_fetch_http_error:{type(exc).__name__}",
                network_error=True,
            )

        content_type = response.headers.get("content-type", "")
        if "html" not in content_type and "xml" not in content_type:
            return RawFetchResult(
                url=url,
                final_url=str(response.url),
                fetch_mode=FetchMode.SIMPLE,
                ok=response.is_success,
                http_status=response.status_code,
                error="unsupported_content_type",
                content_type=content_type,
            )

        html = response.text
        text, markdown = html_to_text_and_markdown(html)
        blocked = response.status_code in {401, 403, 429}
        return RawFetchResult(
            url=url,
            final_url=str(response.url),
            fetch_mode=FetchMode.SIMPLE,
            ok=response.is_success,
            http_status=response.status_code,
            title=html_title(html),
            html=html,
            text=text,
            markdown=markdown,
            blocked=blocked,
            content_type=content_type,
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(max(1, SIMPLE_FETCH_RETRIES + 1)),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=1.5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError)),
    )
    def _request_with_retry(self, url: str) -> httpx.Response:
        with self._client() as client:
            return client.get(url)
