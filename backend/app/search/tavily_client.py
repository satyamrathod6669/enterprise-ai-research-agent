from typing import Optional

from app.search.base import BaseSearchClient, SearchResult
from app import config


class TavilySearchClient(BaseSearchClient):
    name = "tavily"

    def __init__(self, api_key: Optional[str] = None):
        from tavily import TavilyClient
        self.api_key = api_key or config.TAVILY_API_KEY
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is not set.")
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 6) -> list[SearchResult]:
        resp = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
        )
        results = []
        for r in resp.get("results", []):
            results.append(SearchResult(
                url=r.get("url", ""),
                title=r.get("title", ""),
                content=r.get("content", ""),
                score=float(r.get("score", 0.0)),
            ))
        return results
