"""搜索相关的数据类型."""

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """搜索结果数据类."""

    title: str
    url: str
    snippet: str
    source: str  # 来源搜索引擎
    rank: int  # 排名
    metadata: dict[str, Any] | None = None


@dataclass
class WebContent:
    """网页内容数据类."""

    url: str
    title: str
    content: str
    html: str | None = None
    metadata: dict[str, Any] | None = None
