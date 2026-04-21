from __future__ import annotations

from ddgs import DDGS

from .models import SearchResponse, SearchResult


class SearchService:
    def search(
        self,
        query: str,
        limit: int = 5,
        region: str = "wt-wt",
        safesearch: str = "moderate",
    ) -> SearchResponse:
        results: list[SearchResult] = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=limit, region=region, safesearch=safesearch):
                href = item.get("href") or item.get("url") or ""
                title = item.get("title") or href
                snippet = item.get("body") or item.get("snippet") or ""
                if not href:
                    continue
                results.append(
                    SearchResult(
                        title=title,
                        url=href,
                        snippet=snippet,
                        source="ddgs",
                    )
                )
        return SearchResponse(query=query, limit=limit, count=len(results), results=results)
