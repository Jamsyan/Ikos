"""Core abstractions and interfaces for Ikos.

包含核心抽象接口：
- ModelProvider: 多模型统一调用接口
- SearchProvider: 搜索引擎抽象接口
- VoteEngine: 多模型投票引擎
"""

from .engine_switcher import (
    EngineConfig,
    EngineSwitcher,
    EngineType,
    create_engine_selector,
    get_engine,
)

# 原生推理引擎核心模块（新增）
from .hardware_detector import (
    EngineMode,
    HardwareDetector,
    HardwareInfo,
    HardwareTier,
    check_minimum_requirements,
    detect_hardware,
    get_hardware_info,
)
from .model_provider import ModelProvider
from .native_inference_engine import (
    NativeEngineBuilder,
    NativeInferenceEngine,
    create_native_engine,
)
from .native_model_loader import NativeModelLoader, load_native_model
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAICompatibleProvider
from .quantization_config import (
    QuantizationConfig,
    QuantizationLevel,
    QuantizationRecommendation,
    auto_recommend_quantization,
    get_quantization_config,
)
from .search_provider import PlaywrightSearchProvider, SearchProvider
from .vote_engine import VoteEngine, VotingConfig
from .vram_manager import MemoryMonitor, Priority, VRAMConfig, VRAMManager, VRAMPool

__all__ = [
    # engine_switcher
    "EngineConfig",
    "EngineSwitcher",
    "EngineType",
    "create_engine_selector",
    "get_engine",
    # hardware_detector
    "EngineMode",
    "HardwareDetector",
    "HardwareInfo",
    "HardwareTier",
    "check_minimum_requirements",
    "detect_hardware",
    "get_hardware_info",
    # model_provider
    "ModelProvider",
    # native_inference_engine
    "NativeEngineBuilder",
    "NativeInferenceEngine",
    "create_native_engine",
    # native_model_loader
    "NativeModelLoader",
    "load_native_model",
    # providers
    "OllamaProvider",
    "OpenAICompatibleProvider",
    # quantization_config
    "QuantizationConfig",
    "QuantizationLevel",
    "QuantizationRecommendation",
    "auto_recommend_quantization",
    "get_quantization_config",
    # search_provider
    "PlaywrightSearchProvider",
    "SearchProvider",
    # vote_engine
    "VoteEngine",
    "VotingConfig",
    # vram_manager
    "MemoryMonitor",
    "Priority",
    "VRAMConfig",
    "VRAMManager",
    "VRAMPool",
]
