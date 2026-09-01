from app.search.base import BaseSearchClient, SearchResult


class DuckDuckGoSearchClient(BaseSearchClient):
    """Zero-setup fallback: no API key required at all. Used automatically
    when TAVILY_API_KEY is missing, so the app runs end-to-end with ZERO
    external keys configured (only the LLM key is then strictly required)."""
    name = "duckduckgo"

    def search(self, query: str, max_results: int = 6) -> list[SearchResult]:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                results.append(SearchResult(
                    url=r.get("href", ""),
                    title=r.get("title", ""),
                    content=r.get("body", ""),
                    score=1.0 - (i * 0.05),  # rough rank-based score, best-effort
                ))
        return results
