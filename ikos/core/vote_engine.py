"""Vote Engine - 多模型投票引擎.

实现多模型投票决策机制：
- 多数投票策略
- 加权投票策略
- 结果汇总与决策
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class VotingConfig:
    """投票配置."""

    strategy: str = "majority"  # majority, weighted
    min_agreement: float = 0.5  # 最小一致比例
    weights: dict[str, float] | None = None  # 模型权重


class VoteEngine:
    """多模型投票引擎."""

    def __init__(self, config: VotingConfig | None = None):
        """初始化投票引擎.

        Args:
            config: 投票配置
        """
        self.config = config or VotingConfig()

    def aggregate(
        self,
        results: list[Any],
        strategy: str | None = None,
    ) -> dict[str, Any]:
        """汇总投票结果.

        Args:
            results: 模型响应列表
            strategy: 投票策略

        Returns:
            dict: 汇总结果
        """
        strategy = strategy or self.config.strategy

        if strategy == "majority":
            return self._majority_vote(results)
        elif strategy == "weighted":
            return self._weighted_vote(results)
        else:
            logger.warning(f"未知的投票策略：{strategy}，使用默认策略")
            return self._majority_vote(results)

    def _majority_vote(self, results: list[Any]) -> dict[str, Any]:
        """多数投票.

        Args:
            results: 模型响应列表

        Returns:
            dict: 投票结果
        """
        if not results:
            return {"winner": None, "content": "", "confidence": 0.0}

        # 简单实现：返回第一个结果
        # 实际应该实现更复杂的投票逻辑
        winner = results[0]
        confidence = 1.0 / len(results)

        return {
            "winner": winner.model if hasattr(winner, "model") else "unknown",
            "content": winner.content if hasattr(winner, "content") else str(winner),
            "confidence": confidence,
            "all_results": results,
        }

    def _weighted_vote(self, results: list[Any]) -> dict[str, Any]:
        """加权投票.

        Args:
            results: 模型响应列表

        Returns:
            dict: 投票结果
        """
        if not results:
            return {"winner": None, "content": "", "confidence": 0.0}

        weights = self.config.weights or {}

        # 找到权重最高的模型
        best_result = None
        best_weight = -1

        for result in results:
            model_name = result.model if hasattr(result, "model") else "unknown"
            weight = weights.get(model_name, 1.0)

            if weight > best_weight:
                best_weight = weight
                best_result = result

        if best_result is None:
            best_result = results[0]

        return {
            "winner": best_result.model if hasattr(best_result, "model") else "unknown",
            "content": best_result.content
            if hasattr(best_result, "content")
            else str(best_result),
            "confidence": best_weight,
            "all_results": results,
        }

    def calculate_agreement(self, results: list[Any]) -> float:
        """计算一致性比例.

        Args:
            results: 模型响应列表

        Returns:
            float: 一致性比例（0-1）
        """
        if len(results) <= 1:
            return 1.0

        # 简化实现：比较内容相似度
        # 实际应该使用更复杂的相似度算法
        contents = [
            r.content if hasattr(r, "content") else str(r) for r in results
        ]

        # 计算有多少对是相同的
        same_pairs = 0
        total_pairs = 0

        for i in range(len(contents)):
            for j in range(i + 1, len(contents)):
                total_pairs += 1
                if contents[i] == contents[j]:
                    same_pairs += 1

        return same_pairs / total_pairs if total_pairs > 0 else 0.0

    def should_accept(self, results: list[Any]) -> bool:
        """判断是否应该接受投票结果.

        Args:
            results: 模型响应列表

        Returns:
            bool: 是否接受
        """
        agreement = self.calculate_agreement(results)
        return agreement >= self.config.min_agreement
