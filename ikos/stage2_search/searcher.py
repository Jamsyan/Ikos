"""搜索执行器 - 第二阶段核心组件."""

from pathlib import Path
from typing import Any

from loguru import logger

from ikos.core import ModelProvider, SearchProvider
from ikos.utils.config_loader import load_yaml


class SearchExecutor:
    """搜索执行器。

    执行专项搜索任务，发现并记录信息。
    """

    def __init__(
        self,
        model_provider: ModelProvider,
        search_provider: SearchProvider,
        config_path: str | None = None,
    ):
        """初始化搜索执行器。

        Args:
            model_provider: 模型提供者
            search_provider: 搜索提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        self.search_provider = search_provider

        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "prompts" / "stage2_search.yaml"
            )

        self.prompts = load_yaml(config_path)
        self.found_data: list[dict[str, Any]] = []
        self.memo_items: list[dict[str, Any]] = []

    def execute_task(self, task: dict[str, Any], core_topic: str) -> dict[str, Any]:
        """执行单个搜索任务。

        Args:
            task: 任务定义
            core_topic: 核心主题

        Returns:
            dict: 执行结果
        """
        logger.info(f"执行搜索任务：{task.get('name', 'unknown')}")

        queries = task.get("search_queries", [])

        all_results = []
        for query in queries:
            try:
                results = self.search_provider.search(query, max_results=5)
                all_results.extend(results)
                logger.info(f"查询 '{query}' 找到 {len(results)} 个结果")
            except Exception as e:
                logger.warning(f"搜索失败 {query}: {e}")

        # 处理搜索结果
        processed_data = self._process_results(all_results, core_topic)

        # 添加到总数据
        self.found_data.extend(processed_data["found_data"])
        self.memo_items.extend(processed_data["memo_items"])

        return processed_data

    def _process_results(self, results: list[Any], core_topic: str) -> dict[str, Any]:
        """处理搜索结果。

        Args:
            results: 搜索结果列表
            core_topic: 核心主题

        Returns:
            dict: 处理后的数据
        """
        found_data = []
        memo_items = []

        for _i, result in enumerate(results[:5]):  # 限制处理数量
            # 评估可信度
            reliability = self._estimate_reliability(result)

            found_data.append(
                {
                    "url": result.url,
                    "title": result.title,
                    "content": result.snippet,
                    "reliability": reliability,
                    "source_type": self._classify_source(result.url),
                    "rank": result.rank,
                }
            )

            # 发现潜在的连锁信息（简化实现）
            if "历史" in result.title or "原理" in result.title:
                memo_items.append(
                    {
                        "item": result.title,
                        "relevance": f"与{core_topic}相关",
                        "suggested_action": "继续搜索相关信息",
                    }
                )

        return {"found_data": found_data, "memo_items": memo_items}

    def _estimate_reliability(self, result: Any) -> float:
        """评估结果的可信度。

        Args:
            result: 搜索结果

        Returns:
            float: 可信度评分 (1-5)
        """
        url = result.url.lower()

        # 根据域名评估可信度
        if any(domain in url for domain in [".edu", ".gov", ".ac.cn"]):
            return 5.0
        elif any(domain in url for domain in ["arxiv", "ieee", "nature", "science"]):
            return 5.0
        elif "wikipedia" in url:
            return 4.0
        elif any(domain in url for domain in ["zhihu", "csdn", "juejin"]):
            return 3.0
        else:
            return 2.5

    def _classify_source(self, url: str) -> str:
        """分类来源类型。

        Args:
            url: 来源 URL

        Returns:
            str: 来源类型
        """
        url_lower = url.lower()

        if any(domain in url_lower for domain in [".edu", ".gov", "arxiv"]):
            return "学术论文"
        elif "wikipedia" in url_lower:
            return "百科"
        elif any(domain in url_lower for domain in ["zhihu", "csdn"]):
            return "专业社区"
        elif any(domain in url_lower for domain in ["news", "sina", "163"]):
            return "新闻报道"
        else:
            return "其他"

    def get_all_data(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """获取所有数据。

        Returns:
            tuple: (发现的数据列表，备忘录条目列表)
        """
        return self.found_data, self.memo_items

    def reset(self) -> None:
        """重置执行器状态。"""
        self.found_data = []
        self.memo_items = []
