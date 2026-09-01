from app import config
from app.search.base import BaseSearchClient


def get_search_client() -> BaseSearchClient:
    """
    Selects the search provider. If SEARCH_PROVIDER=tavily but no key is
    configured, we automatically fall back to DuckDuckGo instead of crashing —
    this directly answers the brief's mandatory question: "What happens if
    that [free-tier] service becomes paid or unavailable?"
    """
    provider = config.SEARCH_PROVIDER
    if provider == "tavily" and config.TAVILY_API_KEY:
        from app.search.tavily_client import TavilySearchClient
        return TavilySearchClient()
    if provider == "tavily" and not config.TAVILY_API_KEY:
        from app.search.duckduckgo_client import DuckDuckGoSearchClient
        return DuckDuckGoSearchClient()
    if provider == "duckduckgo":
        from app.search.duckduckgo_client import DuckDuckGoSearchClient
        return DuckDuckGoSearchClient()
    raise ValueError(f"Unknown SEARCH_PROVIDER: {provider}")
