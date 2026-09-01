from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    url: str
    title: str
    content: str  # cleaned text/markdown snippet or full content
    score: float = 0.0


class BaseSearchClient(ABC):
    name: str = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 6) -> list[SearchResult]:
        raise NotImplementedError
