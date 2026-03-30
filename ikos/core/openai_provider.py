"""OpenAI 兼容 API 提供者实现."""

from typing import Any

from loguru import logger

from .model_provider import ModelProvider, ModelResponse, VoteResult


class OpenAICompatibleProvider(ModelProvider):
    """OpenAI 兼容 API 提供者（支持 Ollama、vLLM 等）."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        timeout: int = 120,
    ):
        """初始化 OpenAI 兼容提供者.

        Args:
            base_url: API 基础 URL
            api_key: API 密钥
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._client = None

    @property
    def client(self) -> Any:
        """懒加载 OpenAI 客户端."""
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=self.timeout,
                )
                logger.info(f"OpenAI 兼容客户端已连接：{self.base_url}")
            except ImportError:
                logger.warning("openai 库未安装")
                raise
        return self._client

    def call(self, prompt: str, model: str, **kwargs: Any) -> ModelResponse:
        """调用 OpenAI 兼容模型.

        Args:
            prompt: 输入提示词
            model: 模型名称
            **kwargs: 其他参数（温度、最大 token 数等）

        Returns:
            ModelResponse: 模型响应
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            return ModelResponse(
                content=response.choices[0].message.content,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if response.usage
                else None,
            )
        except Exception as e:
            logger.error(f"OpenAI 兼容 API 调用失败：{e}")
            raise

    def call_batch(
        self, prompt: str, models: list[str], **kwargs: Any
    ) -> list[ModelResponse]:
        """批量调用多个模型.

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
            voting_strategy: 投票策略
            **kwargs: 其他参数

        Returns:
            VoteResult: 投票结果
        """
        responses = self.call_batch(prompt, models, **kwargs)

        if not responses:
            raise ValueError("没有模型返回结果")

        # 简单实现，返回第一个结果
        winner = responses[0]
        return VoteResult(
            winner_model=winner.model,
            winner_content=winner.content,
            all_results=responses,
            vote_scores={r.model: 1.0 for r in responses},
        )

    def add_provider(self, name: str, config: dict[str, Any]) -> None:
        """添加新的模型提供者（不支持动态添加）.

        Args:
            name: 提供者名称
            config: 提供者配置
        """
        logger.warning("OpenAICompatibleProvider 不支持动态添加提供者")

    def list_models(self) -> list[str]:
        """列出可用模型.

        Returns:
            list[str]: 模型名称列表
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"获取模型列表失败：{e}")
            return []
