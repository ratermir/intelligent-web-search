from __future__ import annotations

import httpx

from .config import SIMPLE_FETCH_TIMEOUT, USER_AGENT
from .extract import html_title, html_to_text_and_markdown
from .models import FetchMode, RawFetchResult


class SimpleFetcher:
    def __init__(self) -> None:
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        }

    def fetch(self, url: str) -> RawFetchResult:
        try:
            with httpx.Client(
                headers=self._headers,
                follow_redirects=True,
                timeout=SIMPLE_FETCH_TIMEOUT,
                http2=True,
            ) as client:
                response = client.get(url)
        except httpx.TimeoutException:
            return RawFetchResult(
                url=url,
                fetch_mode=FetchMode.SIMPLE,
                ok=False,
                error="simple_fetch_timeout",
                timed_out=True,
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
