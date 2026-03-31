"""Model Provider - 多模型统一调用抽象接口.

提供统一的模型调用接口，支持：
- Ollama 本地模型调用
- OpenAI 兼容 API
- 多模型并行调用
- 投票决策机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelResponse:
    """模型响应数据类."""

    content: str
    model: str
    usage: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class VoteResult:
    """多模型投票结果."""

    winner_model: str
    winner_content: str
    all_results: list[ModelResponse]
    vote_scores: dict[str, float]


class ModelProvider(ABC):
    """多模型统一调用抽象接口."""

    @abstractmethod
    def call(self, prompt: str, model: str, **kwargs: Any) -> ModelResponse:
        """调用单个模型.

        Args:
            prompt: 输入提示词
            model: 模型名称
            **kwargs: 其他参数（温度、最大 token 数等）

        Returns:
            ModelResponse: 模型响应
        """
        pass

    @abstractmethod
    def call_batch(self, prompt: str, models: list[str], **kwargs: Any) -> list[ModelResponse]:
        """批量调用多个模型.

        Args:
            prompt: 输入提示词
            models: 模型名称列表
            **kwargs: 其他参数

        Returns:
            list[ModelResponse]: 所有模型的响应列表
        """
        pass

    @abstractmethod
    def vote(
        self, prompt: str, models: list[str], voting_strategy: str = "majority", **kwargs: Any
    ) -> VoteResult:
        """多模型投票决策.

        Args:
            prompt: 输入提示词
            models: 参与投票的模型列表
            voting_strategy: 投票策略（majority/weighted 等）
            **kwargs: 其他参数

        Returns:
            VoteResult: 投票结果
        """
        pass

    @abstractmethod
    def add_provider(self, name: str, config: dict[str, Any]) -> None:
        """添加新的模型提供者.

        Args:
            name: 提供者名称
            config: 提供者配置
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """列出所有可用的模型.

        Returns:
            list[str]: 模型名称列表
        """
        pass
