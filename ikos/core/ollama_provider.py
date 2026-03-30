"""Ollama 模型提供者实现."""

from typing import Any

from loguru import logger

from .model_provider import ModelProvider, ModelResponse, VoteResult


class OllamaProvider(ModelProvider):
    """Ollama 本地模型提供者."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120):
        """初始化 Ollama 提供者.

        Args:
            base_url: Ollama 服务地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self._client = None

    @property
    def client(self) -> Any:
        """懒加载 Ollama 客户端."""
        if self._client is None:
            try:
                from ollama import Client

                self._client = Client(host=self.base_url, timeout=self.timeout)
                logger.info(f"Ollama 客户端已连接：{self.base_url}")
            except ImportError:
                logger.warning("ollama 库未安装，无法使用本地模型")
                raise
        return self._client

    def call(self, prompt: str, model: str, **kwargs: Any) -> ModelResponse:
        """调用 Ollama 模型.

        Args:
            prompt: 输入提示词
            model: 模型名称
            **kwargs: 其他参数（温度、最大 token 数等）

        Returns:
            ModelResponse: 模型响应
        """
        try:
            response = self.client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            return ModelResponse(
                content=response["message"]["content"],
                model=model,
                usage={
                    "prompt_tokens": response.get("prompt_eval_count", 0),
                    "completion_tokens": response.get("eval_count", 0),
                    "total_tokens": response.get("prompt_eval_count", 0)
                    + response.get("eval_count", 0),
                },
            )
        except Exception as e:
            logger.error(f"Ollama 调用失败：{e}")
            raise

    def call_batch(
        self, prompt: str, models: list[str], **kwargs: Any
    ) -> list[ModelResponse]:
        """批量调用多个 Ollama 模型.

        Args:
            prompt: 输入提示词
            models: 模型名称列表
            **kwargs: 其他参数

        Returns:
            list[ModelResponse]: 所有模型的响应列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(self.call, prompt, model, **kwargs): model
                for model in models
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    model = futures[future]
                    logger.error(f"模型 {model} 调用失败：{e}")

        return results

    def vote(
        self,
        prompt: str,
        models: list[str],
        voting_strategy: str = "majority",
        **kwargs: Any,
    ) -> VoteResult:
        """多模型投票决策.

        Args:
            prompt: 输入提示词
            models: 参与投票的模型列表
            voting_strategy: 投票策略（majority/weighted）
            **kwargs: 其他参数

        Returns:
            VoteResult: 投票结果
        """
        # 获取所有模型响应
        responses = self.call_batch(prompt, models, **kwargs)

        if not responses:
            raise ValueError("没有模型返回结果")

        # 简单多数投票
        if voting_strategy == "majority":
            # 这里简化实现，实际应该更复杂的投票逻辑
            winner = responses[0]  # 暂时返回第一个
            return VoteResult(
                winner_model=winner.model,
                winner_content=winner.content,
                all_results=responses,
                vote_scores={r.model: 1.0 for r in responses},
            )
        else:
            # 加权投票（待实现）
            logger.warning(f"不支持的投票策略：{voting_strategy}，使用默认策略")
            winner = responses[0]
            return VoteResult(
                winner_model=winner.model,
                winner_content=winner.content,
                all_results=responses,
                vote_scores={r.model: 1.0 for r in responses},
            )

    def add_provider(self, name: str, config: dict[str, Any]) -> None:
        """添加新的模型提供者（Ollama 不支持动态添加）.

        Args:
            name: 提供者名称
            config: 提供者配置
        """
        logger.warning("OllamaProvider 不支持动态添加提供者")

    def list_models(self) -> list[str]:
        """列出 Ollama 可用的模型.

        Returns:
            list[str]: 模型名称列表
        """
        try:
            models_response = self.client.list()
            return [model["name"] for model in models_response.get("models", [])]
        except Exception as e:
            logger.error(f"获取模型列表失败：{e}")
            return []
