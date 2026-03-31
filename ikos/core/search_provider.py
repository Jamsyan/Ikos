"""Search Provider - 搜索引擎抽象接口.

提供统一的搜索引擎接口，支持：
- Playwright 浏览器自动化搜索
- 多搜索引擎适配（Google/Bing/百度等）
- 网页内容抓取
- 搜索结果结构化
"""

from .playwright_search import PlaywrightSearchProvider
from .search_provider_base import SearchProvider
from .types import SearchResult, WebContent

__all__ = [
    "SearchProvider",
    "SearchResult",
    "WebContent",
    "PlaywrightSearchProvider",
]