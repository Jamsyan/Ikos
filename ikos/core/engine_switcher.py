"""引擎切换器 - 根据硬件自动选择引擎模式."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union

from loguru import logger

from .hardware_detector import EngineMode, HardwareInfo, detect_hardware
from .model_provider import ModelProvider
from .native_inference_engine import NativeInferenceEngine
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAICompatibleProvider
from .quantization_config import QuantizationConfig


class EngineType(Enum):
    """引擎类型."""

    NATIVE = "原生引擎"
    OLLAMA = "Ollama"
    OPENAI_COMPATIBLE = "OpenAI 兼容"
    HYBRID = "混合模式"


@dataclass
class EngineConfig:
    """引擎配置."""

    # 引擎类型
    engine_type: EngineType

    # 引擎实例
    engine: Optional[ModelProvider] = None

    # 配置参数
    config: dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class EngineSwitcher:
    """引擎切换器.

    功能:
    - 根据硬件自动选择引擎模式
    - 支持手动覆盖
    - 引擎热切换
    - 多引擎统一管理
    """

    def __init__(self, auto_detect: bool = True):
        """初始化引擎切换器.

        Args:
            auto_detect: 是否自动检测硬件
        """
        self._hardware_info: Optional[HardwareInfo] = None
        self._current_engine: Optional[EngineConfig] = None
        self._engines: dict[EngineType, EngineConfig] = {}

        # 硬件检测
        if auto_detect:
            self._hardware_info = detect_hardware()
            logger.info(f"硬件检测完成：{self._hardware_info.tier.value}")

        # 注册引擎
        self._register_default_engines()

    def _register_default_engines(self) -> None:
        """注册默认引擎."""
        # 原生引擎
        self._engines[EngineType.NATIVE] = EngineConfig(
            engine_type=EngineType.NATIVE,
            config={},
        )

        # Ollama 引擎
        self._engines[EngineType.OLLAMA] = EngineConfig(
            engine_type=EngineType.OLLAMA,
            config={
                "base_url": "http://localhost:11434",
                "timeout": 120,
            },
        )

        # OpenAI 兼容引擎
        self._engines[EngineType.OPENAI_COMPATIBLE] = EngineConfig(
            engine_type=EngineType.OPENAI_COMPATIBLE,
            config={
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
            },
        )

        logger.info(f"已注册 {len(self._engines)} 个引擎")

    def select_engine(
        self,
        engine_type: Optional[EngineType] = None,
        mode: Optional[EngineMode] = None,
        manual_override: bool = False,
    ) -> EngineConfig:
        """选择引擎.

        Args:
            engine_type: 引擎类型（None 表示自动选择）
            mode: 引擎模式（None 表示根据硬件自动选择）
            manual_override: 是否手动覆盖

        Returns:
            EngineConfig: 选中的引擎配置
        """
        # 手动指定引擎类型
        if engine_type is not None:
            logger.info(f"手动选择引擎：{engine_type.value}")
            return self._get_or_create_engine(engine_type)

        # 根据模式选择
        if mode is not None:
            engine_type = self._mode_to_engine_type(mode)
            logger.info(f"根据模式选择引擎：{mode.value} -> {engine_type.value}")
            return self._get_or_create_engine(engine_type)

        # 自动选择（根据硬件）
        if self._hardware_info is None:
            self._hardware_info = detect_hardware()

        recommended_mode = self._hardware_info.recommended_mode

        if not manual_override:
            logger.info(f"自动选择引擎：{recommended_mode.value}")
        else:
            logger.info(f"手动覆盖，使用推荐引擎：{recommended_mode.value}")

        engine_type = self._mode_to_engine_type(recommended_mode)
        return self._get_or_create_engine(engine_type)

    def _mode_to_engine_type(self, mode: EngineMode) -> EngineType:
        """将引擎模式转换为引擎类型.

        Args:
            mode: 引擎模式

        Returns:
            EngineType: 引擎类型
        """
        if mode == EngineMode.NATIVE:
            return EngineType.NATIVE
        elif mode == EngineMode.HYBRID:
            # 混合模式：简单任务用原生，复杂任务用 Ollama
            # 这里默认返回原生引擎
            return EngineType.NATIVE
        else:  # EXTERNAL
            # 外部引擎：优先 Ollama
            return EngineType.OLLAMA

    def _get_or_create_engine(self, engine_type: EngineType) -> EngineConfig:
        """获取或创建引擎.

        Args:
            engine_type: 引擎类型

        Returns:
            EngineConfig: 引擎配置
        """
        if engine_type not in self._engines:
            raise ValueError(f"不支持的引擎类型：{engine_type}")

        engine_config = self._engines[engine_type]

        # 如果引擎已创建，直接返回
        if engine_config.engine is not None:
            logger.info(f"引擎已创建：{engine_type.value}")
            return engine_config

        # 创建引擎
        logger.info(f"创建引擎：{engine_type.value}")
        engine_config.engine = self._create_engine(engine_type, engine_config.config)

        return engine_config

    def _create_engine(
        self,
        engine_type: EngineType,
        config: dict[str, Any],
    ) -> ModelProvider:
        """创建引擎实例.

        Args:
            engine_type: 引擎类型
            config: 引擎配置

        Returns:
            ModelProvider: 引擎实例
        """
        if engine_type == EngineType.NATIVE:
            return self._create_native_engine(config)
        elif engine_type == EngineType.OLLAMA:
            return OllamaProvider(
                base_url=config.get("base_url", "http://localhost:11434"),
                timeout=config.get("timeout", 120),
            )
        elif engine_type == EngineType.OPENAI_COMPATIBLE:
            return OpenAICompatibleProvider(
                base_url=config.get("base_url", "http://localhost:11434/v1"),
                api_key=config.get("api_key", "ollama"),
            )
        else:
            raise ValueError(f"不支持的引擎类型：{engine_type}")

    def _create_native_engine(self, config: dict[str, Any]) -> NativeInferenceEngine:
        """创建原生引擎.

        Args:
            config: 引擎配置

        Returns:
            NativeInferenceEngine: 原生引擎实例
        """
        from .native_inference_engine import create_native_engine

        quantization = config.get("quantization", "auto")
        cache_dir = config.get("cache_dir", None)

        return create_native_engine(
            quantization=quantization,
            cache_dir=cache_dir,
        )

    def get_current_engine(self) -> Optional[ModelProvider]:
        """获取当前引擎.

        Returns:
            Optional[ModelProvider]: 当前引擎实例
        """
        if self._current_engine is None:
            return None
        return self._current_engine.engine

    def switch_to(
        self,
        engine_type: EngineType,
        **config_updates: Any,
    ) -> ModelProvider:
        """切换到指定引擎.

        Args:
            engine_type: 引擎类型
            **config_updates: 配置更新

        Returns:
            ModelProvider: 新的引擎实例
        """
        logger.info(f"切换到引擎：{engine_type.value}")

        # 更新配置
        if engine_type in self._engines:
            self._engines[engine_type].config.update(config_updates)

        # 创建新引擎
        engine_config = self._get_or_create_engine(engine_type)
        self._current_engine = engine_config

        logger.info(f"引擎切换完成：{engine_type.value}")
        return engine_config.engine

    def get_engine_info(self) -> dict[str, Any]:
        """获取引擎信息.

        Returns:
            dict: 引擎信息
        """
        info = {
            "hardware_info": self._hardware_info.to_dict() if self._hardware_info else None,
            "current_engine": self._current_engine.engine_type.value if self._current_engine else None,
            "available_engines": [e.value for e in self._engines.keys()],
        }

        if self._current_engine and self._current_engine.engine:
            if isinstance(self._current_engine.engine, NativeInferenceEngine):
                info["vram_usage"] = self._current_engine.engine.get_vram_usage()

        return info

    def log_status(self) -> None:
        """记录引擎状态."""
        logger.info("=" * 60)
        logger.info("引擎切换器状态")
        logger.info("=" * 60)

        if self._hardware_info:
            logger.info(f"硬件：{self._hardware_info.tier.value}")
            logger.info(f"推荐：{self._hardware_info.recommended_mode.value}")

        if self._current_engine:
            logger.info(f"当前引擎：{self._current_engine.engine_type.value}")
        else:
            logger.info("当前引擎：未选择")

        logger.info(f"可用引擎：{', '.join([e.value for e in self._engines.keys()])}")
        logger.info("=" * 60)


@dataclass
class EngineSelectorConfig:
    """引擎选择器配置."""

    # 自动检测硬件
    auto_detect_hardware: bool = True

    # 默认引擎类型
    default_engine: EngineType = EngineType.NATIVE

    # 量化等级（原生引擎）
    quantization: str = "auto"

    # 缓存目录
    cache_dir: str = "./data/models"

    # Ollama 配置
    ollama_base_url: str = "http://localhost:11434"

    # OpenAI 兼容 API 配置
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"


def create_engine_selector(config: Optional[EngineSelectorConfig] = None) -> EngineSwitcher:
    """创建引擎选择器.

    Args:
        config: 配置

    Returns:
        EngineSwitcher: 引擎切换器
    """
    if config is None:
        config = EngineSelectorConfig()

    switcher = EngineSwitcher(auto_detect=config.auto_detect_hardware)

    # 更新配置
    if config.default_engine:
        switcher._engines[config.default_engine].config.update(
            {
                "quantization": config.quantization,
                "cache_dir": config.cache_dir,
            }
        )

    switcher._engines[EngineType.OLLAMA].config["base_url"] = config.ollama_base_url
    switcher._engines[EngineType.OPENAI_COMPATIBLE].config.update(
        {
            "base_url": config.openai_base_url,
            "api_key": config.openai_api_key,
        }
    )

    return switcher


def get_engine(
    preferred_engine: Optional[str] = None,
    quantization: str = "auto",
) -> tuple[ModelProvider, EngineType]:
    """获取引擎（便捷函数）.

    Args:
        preferred_engine: 首选引擎（native/ollama/openai）
        quantization: 量化等级

    Returns:
        tuple: (引擎实例，引擎类型)
    """
    switcher = EngineSwitcher()

    # 解析首选引擎
    engine_type_map = {
        "native": EngineType.NATIVE,
        "ollama": EngineType.OLLAMA,
        "openai": EngineType.OPENAI_COMPATIBLE,
    }

    if preferred_engine and preferred_engine.lower() in engine_type_map:
        engine_type = engine_type_map[preferred_engine.lower()]
    else:
        engine_type = None

    # 选择引擎
    engine_config = switcher.select_engine(
        engine_type=engine_type,
        manual_override=(preferred_engine is not None),
    )

    # 更新原生引擎配置
    if engine_type == EngineType.NATIVE:
        engine_config.config["quantization"] = quantization

    engine = switcher.get_current_engine()

    return engine, engine_config.engine_type
