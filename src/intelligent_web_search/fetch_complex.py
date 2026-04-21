from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from .config import BROWSER_EXTRA_WAIT_MS, BROWSER_WAIT_UNTIL, COMPLEX_FETCH_CONCURRENCY, COMPLEX_FETCH_TIMEOUT, HEADLESS, USER_AGENT
from .extract import html_title, html_to_text_and_markdown
from .models import FetchMode, RawFetchResult


class ComplexFetcher:
    def __init__(self) -> None:
        self._browser: Browser | None = None
        self._playwright = None
        self._lock = asyncio.Semaphore(COMPLEX_FETCH_CONCURRENCY)

    async def startup(self) -> None:
        if self._browser is not None:
            return
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=HEADLESS)

    async def shutdown(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    @asynccontextmanager
    async def _context(self):
        assert self._browser is not None
        context: BrowserContext = await self._browser.new_context(user_agent=USER_AGENT)
        page: Page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()

    async def fetch(self, url: str) -> RawFetchResult:
        await self.startup()
        async with self._lock:
            try:
                async with self._context() as page:
                    response = await page.goto(
                        url,
                        wait_until=BROWSER_WAIT_UNTIL,
                        timeout=int(COMPLEX_FETCH_TIMEOUT * 1000),
                    )
                    if BROWSER_EXTRA_WAIT_MS > 0:
                        await page.wait_for_timeout(BROWSER_EXTRA_WAIT_MS)
                    html = await page.content()
                    title = await page.title()
                    final_url = page.url
                    text, markdown = html_to_text_and_markdown(html)
                    return RawFetchResult(
                        url=url,
                        final_url=final_url,
                        fetch_mode=FetchMode.COMPLEX,
                        ok=response.ok if response else True,
                        http_status=response.status if response else None,
                        title=title or html_title(html),
                        html=html,
                        text=text,
                        markdown=markdown,
                        blocked=(response.status in {401, 403, 429} if response else False),
                        content_type=(response.headers.get("content-type") if response else None),
                    )
            except PlaywrightTimeoutError:
                return RawFetchResult(
                    url=url,
                    fetch_mode=FetchMode.COMPLEX,
                    ok=False,
                    error="complex_fetch_timeout",
                    timed_out=True,
                    network_error=True,
                )
            except Exception as exc:
                return RawFetchResult(
                    url=url,
                    fetch_mode=FetchMode.COMPLEX,
                    ok=False,
                    error=f"complex_fetch_error:{type(exc).__name__}",
                    network_error=True,
                )
