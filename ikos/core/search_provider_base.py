"""Search Provider 抽象基类."""

from abc import ABC, abstractmethod

from .types import SearchResult, WebContent


class SearchProvider(ABC):
    """搜索引擎抽象接口."""

    @abstractmethod
    def search(
        self, query: str, max_results: int = 10, engine: str = "auto"
    ) -> list[SearchResult]:
        """执行搜索."""
        pass

    @abstractmethod
    def fetch_content(self, url: str, extract_text: bool = True) -> WebContent:
        """抓取网页内容."""
        pass

    @abstractmethod
    def search_and_fetch(
        self, query: str, max_results: int = 5, engine: str = "auto"
    ) -> list[WebContent]:
        """搜索并抓取内容."""
        pass

    @abstractmethod
    def add_api_provider(self, name: str, config: dict) -> None:
        """添加 API 搜索提供者."""
        pass

    @abstractmethod
    def list_engines(self) -> list[str]:
        """列出所有支持的搜索引擎."""
        pass
