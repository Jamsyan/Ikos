"""原生模型加载器 - 从魔塔社区/HuggingFace 加载模型."""

from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .hardware_detector import HardwareInfo
from .quantization_config import (QuantizationConfig, QuantizationLoader,
                                  auto_recommend_quantization)
from .vram_manager import VRAMManager


class NativeModelLoader:
    """原生模型加载器.

    功能:
    - 从魔塔社区/HuggingFace 下载模型
    - 支持断点续传
    - 自动选择量化等级加载
    - 模型缓存管理
    - 支持 CPU-GPU 混合加载
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        hardware_info: Optional[HardwareInfo] = None,
        vram_manager: Optional[VRAMManager] = None,
    ):
        """初始化模型加载器.

        Args:
            cache_dir: 模型缓存目录
            hardware_info: 硬件信息
            vram_manager: 显存管理器
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./data/models")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.hardware_info = hardware_info
        self.vram_manager = vram_manager

        # 延迟加载
        self._loaded_models: dict[str, Any] = {}
        self._model_configs: dict[str, QuantizationConfig] = {}

        logger.info(f"原生模型加载器已初始化，缓存目录：{self.cache_dir}")

    def download_model(
        self,
        model_name: str,
        revision: str = "main",
        quantization: Optional[str] = None,
    ) -> Path:
        """下载模型.

        Args:
            model_name: 模型名称（如 "Qwen/Qwen2.5-7B-Instruct"）
            revision: 版本分支
            quantization: 量化等级（NF4/INT4/INT8/FP16/FP32），None 表示自动推荐

        Returns:
            Path: 模型本地路径
        """
        from ikos.utils.model_downloader import ModelDownloader

        logger.info(f"开始下载模型：{model_name}")

        # 自动推荐量化等级
        if quantization is None:
            if self.hardware_info is None:
                from .hardware_detector import detect_hardware

                self.hardware_info = detect_hardware()

            quant_config = auto_recommend_quantization(model_name, self.hardware_info)
            quantization = quant_config.level.value
            logger.info(f"自动推荐量化等级：{quantization}")

        # 构建下载器
        downloader = ModelDownloader(cache_dir=str(self.cache_dir))

        # 检查是否已缓存
        cached_path = downloader.get_model_path(model_name, revision)
        if cached_path:
            logger.info(f"模型已缓存：{cached_path}")
            return cached_path

        # 确定需要下载的文件（根据量化等级）
        allow_patterns = self._get_download_patterns(quantization)

        # 下载模型
        try:
            model_path = downloader.download(
                model_id=model_name,
                revision=revision,
                allow_patterns=allow_patterns,
                ignore_patterns=["*.msgpack", "*.h5"],  # 忽略其他格式
                resume_download=True,
            )

            logger.info(f"模型下载完成：{model_path}")
            return model_path

        except Exception as e:
            logger.error(f"模型下载失败：{e}")
            raise

    def load_model(
        self,
        model_name: str,
        model_path: Optional[Path] = None,
        quantization: Optional[str] = None,
        revision: str = "main",
    ) -> tuple[Any, Any]:
        """加载模型.

        Args:
            model_name: 模型名称
            model_path: 模型本地路径（None 表示先下载）
            quantization: 量化等级
            revision: 版本分支

        Returns:
            tuple: (model, tokenizer)
        """
        # 检查是否已加载
        if model_name in self._loaded_models:
            logger.info(f"模型已加载：{model_name}")
            return self._loaded_models[model_name]

        # 下载模型（如果未提供路径）
        if model_path is None:
            model_path = self.download_model(model_name, revision, quantization)

        # 确定量化等级
        if quantization is None:
            quant_config = auto_recommend_quantization(model_name, self.hardware_info)
            quantization = quant_config.level.value
        else:
            from .quantization_config import get_quantization_config

            quant_config = get_quantization_config(quantization)

        logger.info(f"加载模型：{model_name} ({quantization})")

        # 分配显存
        if self.vram_manager:
            model_size = self._estimate_model_size(model_name, quant_config)
            if not self.vram_manager.allocate(model_size, model_name):
                logger.warning(f"显存不足，尝试 CPU-GPU 混合加载")

        # 获取加载配置
        load_config = QuantizationLoader.get_load_config(quant_config, str(model_path))

        # 加载模型和分词器
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # 加载分词器
            logger.info("加载分词器...")
            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True,
            )

            # 加载模型
            logger.info("加载模型...")
            model = AutoModelForCausalLM.from_pretrained(**load_config, trust_remote_code=True)

            # 评估模型
            model.eval()

            logger.info(f"模型加载成功：{model_name}")

            # 保存加载信息
            self._loaded_models[model_name] = (model, tokenizer)
            self._model_configs[model_name] = quant_config

            return model, tokenizer

        except ImportError as e:
            logger.error(f"依赖库未安装：{e}")
            logger.error("请运行：pip install torch transformers accelerate bitsandbytes")
            raise

        except Exception as e:
            logger.error(f"模型加载失败：{e}")

            # 尝试降级
            if quantization != "FP32":
                logger.info("尝试降级加载（FP32）...")
                return self.load_model(model_name, model_path, "FP32", revision)
            else:
                raise

    def unload_model(self, model_name: str) -> bool:
        """卸载模型.

        Args:
            model_name: 模型名称

        Returns:
            bool: 是否成功卸载
        """
        if model_name not in self._loaded_models:
            logger.warning(f"模型未加载：{model_name}")
            return False

        import gc

        import torch

        model, tokenizer = self._loaded_models.pop(model_name)

        # 删除模型
        del model
        del tokenizer

        # 清理 CUDA 缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # 释放显存
        if self.vram_manager:
            self.vram_manager.release(model_name)

        # 垃圾回收
        gc.collect()

        logger.info(f"模型已卸载：{model_name}")
        return True

    def get_cached_models(self) -> list[dict]:
        """获取已缓存的模型列表.

        Returns:
            list[dict]: 模型信息列表
        """
        from ikos.utils.cache_manager import ModelCacheManager

        cache_manager = ModelCacheManager(str(self.cache_dir))
        return cache_manager.list_cached_models()

    def _get_download_patterns(self, quantization: str) -> list[str]:
        """根据量化等级获取下载文件模式.

        Args:
            quantization: 量化等级

        Returns:
            list[str]: 文件模式列表
        """
        # 基础文件（必须）
        patterns = [
            "*.json",  # 配置文件
            "*.txt",  # 分词器文件
            "*.model",  # 分词器模型
            "tokenizer.*",
        ]

        # 根据量化等级添加模型文件
        if quantization in ["NF4", "INT4"]:
            # 4bit 量化
            patterns.extend(
                [
                    "*.safetensors",  # 优先 safetensors 格式
                    "pytorch_model*.bin",
                ]
            )
        elif quantization == "INT8":
            # 8bit 量化
            patterns.extend(
                [
                    "*.safetensors",
                    "pytorch_model*.bin",
                ]
            )
        elif quantization == "FP16":
            # FP16
            patterns.extend(
                [
                    "model*.safetensors",
                    "pytorch_model*.bin",
                ]
            )
        else:
            # FP32（全量）
            patterns.append("*.safetensors")
            patterns.append("pytorch_model*.bin")

        return patterns

    def _estimate_model_size(self, model_name: str, quant_config: QuantizationConfig) -> float:
        """估算模型大小（GB）.

        Args:
            model_name: 模型名称
            quant_config: 量化配置

        Returns:
            float: 模型大小（GB）
        """
        # 从模型名称提取参数量
        import re

        match = re.search(r"(\d+(?:\.\d+)?)[bB]", model_name)
        if not match:
            # 默认 7B
            params_b = 7.0
        else:
            params_b = float(match.group(1))

        # 计算显存占用
        return quant_config.calculate_memory_usage(params_b)

    def get_loaded_models(self) -> list[str]:
        """获取已加载的模型列表.

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
        if model_name not in self._loaded_models:
            return None

        config = self._model_configs.get(model_name)

        return {
            "name": model_name,
            "quantization": config.level.value if config else "unknown",
            "loaded": True,
        }

    def __del__(self):
        """析构函数，卸载所有模型."""
        for model_name in list(self._loaded_models.keys()):
            try:
                self.unload_model(model_name)
            except Exception:
                pass


def load_native_model(
    model_name: str,
    cache_dir: Optional[str] = None,
    quantization: Optional[str] = None,
    **kwargs: Any,
) -> tuple[Any, Any]:
    """便捷函数：加载原生模型.

    Args:
        model_name: 模型名称
        cache_dir: 缓存目录
        quantization: 量化等级
        **kwargs: 其他参数

    Returns:
        tuple: (model, tokenizer)
    """
    loader = NativeModelLoader(cache_dir=cache_dir, **kwargs)
    return loader.load_model(model_name, quantization=quantization)
