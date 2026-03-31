"""Core abstractions and interfaces for Ikos.

包含核心抽象接口：
- ModelProvider: 多模型统一调用接口
- SearchProvider: 搜索引擎抽象接口
- VoteEngine: 多模型投票引擎
- NativeInferenceEngine: 原生推理引擎
"""

from .model_provider import ModelProvider
from .search_provider import SearchProvider, PlaywrightSearchProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAICompatibleProvider
from .vote_engine import VoteEngine, VotingConfig

# 原生推理引擎核心模块（新增）
from .hardware_detector import (
    HardwareDetector,
    HardwareInfo,
    HardwareTier,
    EngineMode,
    detect_hardware,
    get_hardware_info,
    check_minimum_requirements,
)
from .vram_manager import (
    VRAMManager,
    VRAMPool,
    MemoryMonitor,
    VRAMConfig,
    Priority,
)
from .quantization_config import (
    QuantizationConfig,
    QuantizationLevel,
    QuantizationRecommendation,
    auto_recommend_quantization,
    get_quantization_config,
)
from .native_model_loader import NativeModelLoader, load_native_model
from .native_inference_engine import (
    NativeInferenceEngine,
    NativeEngineBuilder,
    create_native_engine,
)
from .engine_switcher import (
    EngineSwitcher,
    EngineType,
    EngineConfig,
    create_engine_selector,
    get_engine,
)

__all__ = [
    # 原有导出
    "ModelProvider",
    "SearchProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "PlaywrightSearchProvider",
    "VoteEngine",
    "VotingConfig",
    
    # 原生推理引擎导出（新增）
    # 硬件检测
    "HardwareDetector",
    "HardwareInfo",
    "HardwareTier",
    "EngineMode",
    "detect_hardware",
    "get_hardware_info",
    "check_minimum_requirements",
    
    # 显存管理
    "VRAMManager",
    "VRAMPool",
    "MemoryMonitor",
    "VRAMConfig",
    "Priority",
    
    # 量化配置
    "QuantizationConfig",
    "QuantizationLevel",
    "QuantizationRecommendation",
    "auto_recommend_quantization",
    "get_quantization_config",
    
    # 模型加载
    "NativeModelLoader",
    "load_native_model",
    
    # 推理引擎
    "NativeInferenceEngine",
    "NativeEngineBuilder",
    "create_native_engine",
    
    # 引擎切换
    "EngineSwitcher",
    "EngineType",
    "EngineConfig",
    "create_engine_selector",
    "get_engine",
]
