"""原生推理引擎集成测试."""

import pytest

from ikos.core.native_inference_engine import (
    NativeInferenceEngine,
    NativeEngineBuilder,
    create_native_engine,
)
from ikos.core.engine_switcher import (
    EngineSwitcher,
    EngineType,
    create_engine_selector,
    get_engine,
)
from ikos.core.hardware_detector import detect_hardware


class TestNativeEngineBuilder:
    """测试原生引擎构建器."""

    def test_builder_initialization(self):
        """测试构建器初始化."""
        builder = NativeEngineBuilder()
        
        assert builder is not None
        assert builder._hardware_info is None
        assert builder._quant_config is None

    def test_builder_fluent_api(self):
        """测试流式 API."""
        builder = NativeEngineBuilder()
        
        result = builder.with_hardware(detect_hardware())
        assert result is builder  # 返回自身
        
        result = builder.with_quantization("NF4")
        assert result is builder


class TestEngineSwitcher:
    """测试引擎切换器."""

    def test_switcher_initialization(self):
        """测试切换器初始化."""
        switcher = EngineSwitcher(auto_detect=False)
        
        assert switcher is not None
        assert len(switcher._engines) > 0

    def test_select_engine_native(self):
        """测试选择原生引擎."""
        switcher = EngineSwitcher(auto_detect=False)
        
        engine_config = switcher.select_engine(EngineType.NATIVE)
        
        assert engine_config is not None
        assert engine_config.engine_type == EngineType.NATIVE

    def test_get_engine_info(self):
        """测试获取引擎信息."""
        switcher = EngineSwitcher(auto_detect=False)
        
        info = switcher.get_engine_info()
        
        assert isinstance(info, dict)
        assert "available_engines" in info

    def test_switch_to_engine(self):
        """测试切换到引擎."""
        switcher = EngineSwitcher(auto_detect=False)
        
        # 切换到原生引擎
        engine = switcher.switch_to(EngineType.NATIVE)
        
        assert engine is not None


class TestEngineSelectorConfig:
    """测试引擎选择器配置."""

    def test_default_config(self):
        """测试默认配置."""
        from ikos.core.engine_switcher import EngineSelectorConfig
        
        config = EngineSelectorConfig()
        
        assert config.auto_detect_hardware is True
        assert config.default_engine == EngineType.NATIVE
        assert config.quantization == "auto"


class TestCreateEngineSelector:
    """测试创建引擎选择器."""

    def test_create_with_default_config(self):
        """测试使用默认配置创建."""
        switcher = create_engine_selector()
        
        assert switcher is not None

    def test_create_with_custom_config(self):
        """测试使用自定义配置创建."""
        from ikos.core.engine_switcher import EngineSelectorConfig
        
        config = EngineSelectorConfig(
            auto_detect_hardware=False,
            quantization="INT8",
        )
        
        switcher = create_engine_selector(config)
        
        assert switcher is not None


class TestGetEngine:
    """测试获取引擎便捷函数."""

    def test_get_native_engine(self):
        """测试获取原生引擎."""
        engine, engine_type = get_engine(preferred_engine="native")
        
        assert engine is not None
        assert engine_type == EngineType.NATIVE

    def test_get_engine_auto(self):
        """测试自动获取引擎."""
        engine, engine_type = get_engine()
        
        assert engine is not None
        assert engine_type in EngineType


class TestHardwareDetection:
    """测试硬件检测集成."""

    def test_detect_and_use(self):
        """测试检测并使用硬件信息."""
        hardware = detect_hardware()
        
        assert hardware is not None
        assert hardware.tier is not None
        assert hardware.recommended_mode is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
