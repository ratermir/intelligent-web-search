from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from .orchestrator import FetchOrchestrator
from .search import SearchService

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("intelligent_web_search")

mcp = FastMCP("intelligent-web-search")
search_service = SearchService()
orchestrator = FetchOrchestrator()


@mcp.tool()
def search_web(
    query: str,
    limit: int = 5,
    region: str = "wt-wt",
    safesearch: str = "moderate",
) -> dict:
    """Search the public web via ddgs.

    Args:
        query: Search query.
        limit: Maximum number of results.
        region: DDGS region code.
        safesearch: DDGS safesearch mode.
    """
    result = search_service.search(query=query, limit=limit, region=region, safesearch=safesearch)
    return result.model_dump()


@mcp.tool()
async def fetch_content(
    url: str,
    prefer_complex: bool = False,
    debug: bool = False,
) -> dict:
    """Fetch a URL with intelligent routing.

    Flow:
    1. use simple fetch by default
    2. analyze the result with deterministic heuristics
    3. fall back to browser fetch when needed

    Args:
        url: URL to fetch.
        prefer_complex: Skip simple fetch and use browser fetch immediately.
        debug: Include diagnostics payload in the response.
    """
    result = await orchestrator.fetch_content(url=url, prefer_complex=prefer_complex, debug=debug)
    return result.model_dump()


@mcp.tool()
async def smart_retrieve(
    query: str,
    search_limit: int = 5,
    fetch_limit: int = 3,
    debug: bool = False,
) -> dict:
    """Search first, then fetch the top URLs.

    Args:
        query: Search query.
        search_limit: Number of search results to request.
        fetch_limit: Number of URLs to fetch from the search results.
        debug: Include diagnostics in each fetch result.
    """
    search = search_service.search(query=query, limit=search_limit)
    items = []
    for search_result in search.results[:fetch_limit]:
        fetched = await orchestrator.fetch_content(url=search_result.url, debug=debug)
        items.append(
            {
                "search_result": search_result.model_dump(),
                "fetch": fetched.model_dump(),
            }
        )
    return {
        "query": query,
        "search": search.model_dump(),
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Intelligent Web Search MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio"],
        default="stdio",
        help="MCP transport. This build is pinned to stdio for maximum compatibility.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Reserved for future HTTP transport support.")
    parser.add_argument("--port", type=int, default=8000, help="Reserved for future HTTP transport support.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.transport != "stdio":
        raise SystemExit("Only stdio transport is enabled in this build.")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
