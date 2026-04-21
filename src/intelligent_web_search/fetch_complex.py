from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import (
    BROWSER_ABORT_RESOURCE_TYPES,
    BROWSER_EXTRA_WAIT_MS,
    BROWSER_WAIT_UNTIL,
    COMPLEX_FETCH_CONCURRENCY,
    COMPLEX_FETCH_EXTRACT_TIMEOUT,
    COMPLEX_FETCH_NAV_TIMEOUT,
    COMPLEX_FETCH_RETRIES,
    HEADLESS,
    USER_AGENT,
)
from .extract import html_title, html_to_text_and_markdown
from .models import FetchMode, RawFetchResult


class ComplexFetcher:
    def __init__(self) -> None:
        self._browser: Browser | None = None
        self._playwright = None
        self._startup_lock = asyncio.Lock()
        self._lock = asyncio.Semaphore(COMPLEX_FETCH_CONCURRENCY)

    async def startup(self) -> None:
        if self._browser is not None:
            return
        async with self._startup_lock:
            if self._browser is not None:
                return
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=HEADLESS)

    async def shutdown(self) -> None:
        async with self._startup_lock:
            if self._browser is not None:
                await self._safe_close(self._browser)
                self._browser = None
            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None

    async def _safe_close(self, closeable) -> None:
        try:
            await asyncio.wait_for(closeable.close(), timeout=2.0)
        except Exception:
            return

    @asynccontextmanager
    async def _context(self):
        assert self._browser is not None
        context: BrowserContext = await self._browser.new_context(user_agent=USER_AGENT)
        page: Page = await context.new_page()
        await page.route(
            "**/*",
            lambda route: route.abort() if route.request.resource_type in BROWSER_ABORT_RESOURCE_TYPES else route.continue_(),
        )
        try:
            yield page
        finally:
            try:
                await self._safe_close(page)
            finally:
                await self._safe_close(context)

    async def fetch(self, url: str) -> RawFetchResult:
        await self.startup()
        async with self._lock:
            try:
                async for attempt in self._retry_controller():
                    with attempt:
                        return await self._fetch_once(url)
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

    def _retry_controller(self) -> AsyncRetrying:
        return AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(max(1, COMPLEX_FETCH_RETRIES + 1)),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=2.0),
            retry=retry_if_exception_type((PlaywrightTimeoutError, RuntimeError)),
        )

    async def _fetch_once(self, url: str) -> RawFetchResult:
        async with self._context() as page:
            response = await page.goto(
                url,
                wait_until=BROWSER_WAIT_UNTIL,
                timeout=int(COMPLEX_FETCH_NAV_TIMEOUT * 1000),
            )
            if BROWSER_EXTRA_WAIT_MS > 0:
                await page.wait_for_timeout(BROWSER_EXTRA_WAIT_MS)
            html = await asyncio.wait_for(page.content(), timeout=COMPLEX_FETCH_EXTRACT_TIMEOUT)
            title = await asyncio.wait_for(page.title(), timeout=COMPLEX_FETCH_EXTRACT_TIMEOUT)
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
