"""原生推理引擎核心 - 基于 Transformers + PyTorch 的推理引擎."""

import time
from typing import Any, Optional

from loguru import logger

from .hardware_detector import HardwareInfo, detect_hardware
from .model_provider import ModelProvider, ModelResponse, VoteResult
from .native_model_loader import NativeModelLoader
from .quantization_config import (QuantizationConfig,
                                  auto_recommend_quantization)
from .vram_manager import Priority, VRAMManager


class NativeInferenceEngine(ModelProvider):
    """原生推理引擎.

    基于 Transformers + PyTorch 的本地推理引擎：
    - 实现 ModelProvider 接口
    - 支持单轮对话推理
    - 支持批量推理
    - 支持多模型投票
    - 自动显存管理
    - 支持 CPU-GPU 混合推理
    """

    def __init__(
        self,
        hardware_info: Optional[HardwareInfo] = None,
        vram_manager: Optional[VRAMManager] = None,
        quant_config: Optional[QuantizationConfig] = None,
        cache_dir: Optional[str] = None,
    ):
        """初始化原生推理引擎.

        Args:
            hardware_info: 硬件信息
            vram_manager: 显存管理器
            quant_config: 量化配置
            cache_dir: 模型缓存目录
        """
        # 硬件检测
        if hardware_info is None:
            hardware_info = detect_hardware()
            logger.info(f"已检测硬件：{hardware_info.tier.value}")

        self.hardware_info = hardware_info

        # 显存管理
        if vram_manager is None:
            vram_manager = VRAMManager.from_hardware(hardware_info)
        self.vram_manager = vram_manager

        # 量化配置
        self.quant_config = quant_config

        # 模型加载器
        self.model_loader = NativeModelLoader(
            cache_dir=cache_dir,
            hardware_info=hardware_info,
            vram_manager=vram_manager,
        )

        # 已加载的模型
        self._loaded_models: dict[str, tuple[Any, Any]] = {}

        logger.info("原生推理引擎已初始化")
        logger.info(f"硬件：{hardware_info.gpu_model or 'CPU'} ({hardware_info.gpu_memory_gb:.1f}GB)")
        logger.info(f"量化：{quant_config.level.value if quant_config else '自动'}")

    def call(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        **kwargs: Any,
    ) -> ModelResponse:
        """调用单个模型进行推理.

        Args:
            prompt: 输入提示词
            model: 模型名称
            temperature: 温度
            max_tokens: 最大 token 数
            top_p: Top-p 采样
            repetition_penalty: 重复惩罚
            **kwargs: 其他参数

        Returns:
            ModelResponse: 模型响应
        """
        start_time = time.time()

        # 加载模型（如果未加载）
        if model not in self._loaded_models:
            logger.info(f"加载模型：{model}")
            model_obj, tokenizer = self.model_loader.load_model(
                model_name=model,
                quantization=self.quant_config.level.value if self.quant_config else None,
            )
            self._loaded_models[model] = (model_obj, tokenizer)
        else:
            model_obj, tokenizer = self._loaded_models[model]

        # 构建输入
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096,
        )

        # 移动到设备
        import torch

        device = next(model_obj.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # 生成配置
        gen_config = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "do_sample": temperature > 0,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }

        # 推理
        logger.info(f"开始推理：{model} (max_tokens={max_tokens})")

        with torch.no_grad():
            outputs = model_obj.generate(**inputs, **gen_config)

        # 解码输出
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(generated_ids, skip_special_tokens=True)

        # 计算用时
        elapsed = time.time() - start_time

        # 统计 token 数
        input_tokens = inputs["input_ids"].shape[1]
        output_tokens = len(generated_ids)

        logger.info(f"推理完成：{output_tokens} tokens, {elapsed:.2f}s, {output_tokens / elapsed:.1f} tokens/s")

        return ModelResponse(
            content=response,
            model=model,
            usage={
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "elapsed_seconds": elapsed,
                "tokens_per_second": output_tokens / elapsed if elapsed > 0 else 0,
            },
        )

    def call_batch(
        self,
        prompt: str,
        models: list[str],
        **kwargs: Any,
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

        logger.info(f"批量推理：{len(models)} 个模型")

        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(self.call, prompt, model, **kwargs): model
                for model in models
            }

            for future in as_completed(futures):
                model = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"模型 {model} 推理完成")
                except Exception as e:
                    logger.error(f"模型 {model} 推理失败：{e}")

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
        logger.info(f"开始多模型投票：{len(models)} 个模型，策略：{voting_strategy}")

        # 获取所有模型响应
        responses = self.call_batch(prompt, models, **kwargs)

        if not responses:
            raise ValueError("没有模型返回结果")

        # 计算投票分数
        vote_scores = self._calculate_vote_scores(responses, voting_strategy)

        # 选出获胜者
        winner_model = max(vote_scores, key=vote_scores.get)
        winner_response = next(r for r in responses if r.model == winner_model)

        logger.info(f"投票结果：{winner_model} 获胜")

        return VoteResult(
            winner_model=winner_model,
            winner_content=winner_response.content,
            all_results=responses,
            vote_scores=vote_scores,
        )

    def _calculate_vote_scores(
        self,
        responses: list[ModelResponse],
        strategy: str,
    ) -> dict[str, float]:
        """计算投票分数.

        Args:
            responses: 模型响应列表
            strategy: 投票策略

        Returns:
            dict[str, float]: 模型分数
        """
        scores = {}

        if strategy == "majority":
            # 简单多数投票（这里简化实现，根据响应长度和质量评分）
            for response in responses:
                # 简化评分：基于响应长度和 token 速度
                usage = response.usage or {}
                tokens_per_sec = usage.get("tokens_per_second", 0)
                output_tokens = usage.get("completion_tokens", 0)

                # 分数 = token 数 * 速度系数
                score = output_tokens * (1 + tokens_per_sec / 100)
                scores[response.model] = score

        elif strategy == "weighted":
            # 加权投票（基于模型权重）
            # TODO: 从配置中读取模型权重
            for response in responses:
                scores[response.model] = 1.0  # 默认权重

        else:
            logger.warning(f"未知投票策略：{strategy}，使用 majority")
            return self._calculate_vote_scores(responses, "majority")

        return scores

    def add_provider(self, name: str, config: dict[str, Any]) -> None:
        """添加新的模型提供者（原生引擎不支持）.

        Args:
            name: 提供者名称
            config: 提供者配置
        """
        logger.warning("NativeInferenceEngine 不支持动态添加提供者")

    def list_models(self) -> list[str]:
        """列出已加载的模型.

        Returns:
            list[str]: 模型名称列表
        """
        return list(self._loaded_models.keys())

    def get_model_info(self, model_name: str) -> Optional[dict]:
        """获取模型信息.

        Args:
            model_name: 模型名称

        Returns:
            Optional[dict]: 模型信息
        """
        return self.model_loader.get_model_info(model_name)

    def unload_model(self, model_name: str) -> bool:
        """卸载模型.

        Args:
            model_name: 模型名称

        Returns:
            bool: 是否成功卸载
        """
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            return self.model_loader.unload_model(model_name)
        return False

    def unload_all_models(self) -> None:
        """卸载所有模型."""
        for model_name in list(self._loaded_models.keys()):
            self.unload_model(model_name)

    def get_vram_usage(self) -> dict:
        """获取显存使用情况.

        Returns:
            dict: 显存使用信息
        """
        return self.vram_manager.get_usage()

    def log_status(self) -> None:
        """记录引擎状态."""
        logger.info("=" * 60)
        logger.info("原生推理引擎状态")
        logger.info("=" * 60)
        logger.info(f"已加载模型：{len(self._loaded_models)}")
        for model_name in self._loaded_models:
            logger.info(f"  - {model_name}")
        logger.info(f"显存使用：{self.get_vram_usage()}")
        logger.info("=" * 60)


class NativeEngineBuilder:
    """原生引擎构建器（流式 API）."""

    def __init__(self):
        """初始化构建器."""
        self._hardware_info: Optional[HardwareInfo] = None
        self._vram_manager: Optional[VRAMManager] = None
        self._quant_config: Optional[QuantizationConfig] = None
        self._cache_dir: Optional[str] = None

    def with_hardware(self, hardware_info: HardwareInfo) -> "NativeEngineBuilder":
        """设置硬件信息.

        Args:
            hardware_info: 硬件信息

        Returns:
            NativeEngineBuilder: 构建器自身
        """
        self._hardware_info = hardware_info
        return self

    def with_vram_manager(self, vram_manager: VRAMManager) -> "NativeEngineBuilder":
        """设置显存管理器.

        Args:
            vram_manager: 显存管理器

        Returns:
            NativeEngineBuilder: 构建器自身
        """
        self._vram_manager = vram_manager
        return self

    def with_quantization(self, level: str) -> "NativeEngineBuilder":
        """设置量化等级.

        Args:
            level: 量化等级（NF4/INT4/INT8/FP16/FP32）

        Returns:
            NativeEngineBuilder: 构建器自身
        """
        from .quantization_config import get_quantization_config

        self._quant_config = get_quantization_config(level)
        return self

    def with_cache_dir(self, cache_dir: str) -> "NativeEngineBuilder":
        """设置缓存目录.

        Args:
            cache_dir: 缓存目录

        Returns:
            NativeEngineBuilder: 构建器自身
        """
        self._cache_dir = cache_dir
        return self

    def build(self) -> NativeInferenceEngine:
        """构建引擎.

        Returns:
            NativeInferenceEngine: 原生推理引擎
        """
        return NativeInferenceEngine(
            hardware_info=self._hardware_info,
            vram_manager=self._vram_manager,
            quant_config=self._quant_config,
            cache_dir=self._cache_dir,
        )


def create_native_engine(
    quantization: str = "auto",
    cache_dir: Optional[str] = None,
) -> NativeInferenceEngine:
    """创建原生推理引擎（便捷函数）.

    Args:
        quantization: 量化等级（auto/NF4/INT4/INT8/FP16/FP32）
        cache_dir: 缓存目录

    Returns:
        NativeInferenceEngine: 原生推理引擎
    """
    from .hardware_detector import detect_hardware
    from .quantization_config import auto_recommend_quantization

    # 硬件检测
    hardware_info = detect_hardware()
    logger.info(f"硬件检测完成：{hardware_info.tier.value}")

    # 量化配置
    if quantization == "auto":
        quant_config = auto_recommend_quantization("qwen3.5:7b", hardware_info)
    else:
        from .quantization_config import get_quantization_config

        quant_config = get_quantization_config(quantization)

    logger.info(f"量化配置：{quant_config.level.value}")

    # 构建引擎
    engine = NativeInferenceEngine(
        hardware_info=hardware_info,
        quant_config=quant_config,
        cache_dir=cache_dir,
    )

    logger.info("原生推理引擎创建成功")
    return engine
