"""硬件检测模块测试."""

import pytest

from ikos.core.hardware_detector import (
    EngineMode,
    HardwareDetector,
    HardwareInfo,
    HardwareTier,
    check_minimum_requirements,
    detect_hardware,
)


class TestHardwareInfo:
    """测试硬件信息数据类."""

    def test_default_initialization(self):
        """测试默认初始化."""
        info = HardwareInfo()

        assert info.gpu_model is None
        assert info.gpu_memory_gb == 0.0
        assert info.cpu_cores == 0
        assert info.system_memory_gb == 0.0
        assert info.tier == HardwareTier.EXTREME
        assert info.recommended_mode == EngineMode.NATIVE

    def test_classification_extreme(self):
        """测试极限场景分级."""
        info = HardwareInfo(gpu_memory_gb=4.0)
        assert info.tier == HardwareTier.EXTREME
        assert info.recommended_mode == EngineMode.NATIVE

    def test_classification_basic(self):
        """测试基础场景分级."""
        info = HardwareInfo(gpu_memory_gb=8.0)
        assert info.tier == HardwareTier.BASIC
        assert info.recommended_mode == EngineMode.HYBRID

    def test_classification_performance(self):
        """测试性能场景分级."""
        info = HardwareInfo(gpu_memory_gb=16.0)
        assert info.tier == HardwareTier.PERFORMANCE
        assert info.recommended_mode == EngineMode.EXTERNAL

    def test_classification_flagship(self):
        """测试旗舰场景分级."""
        info = HardwareInfo(gpu_memory_gb=24.0)
        assert info.tier == HardwareTier.FLAGSHIP
        assert info.recommended_mode == EngineMode.EXTERNAL

    def test_to_dict(self):
        """测试转换为字典."""
        info = HardwareInfo(
            gpu_model="NVIDIA RTX 3060",
            gpu_memory_gb=12.0,
            cpu_cores=8,
            system_memory_gb=16.0,
        )

        info_dict = info.to_dict()

        assert info_dict["gpu_model"] == "NVIDIA RTX 3060"
        assert info_dict["gpu_memory_gb"] == 12.0
        assert info_dict["tier"] in ["极限场景", "基础场景", "性能场景", "旗舰场景"]

    def test_str_representation(self):
        """测试字符串表示."""
        info = HardwareInfo(
            gpu_model="NVIDIA RTX 3060",
            gpu_memory_gb=12.0,
            cpu_cores=8,
            system_memory_gb=16.0,
        )

        info_str = str(info)

        assert "NVIDIA RTX 3060" in info_str
        assert "12.0" in info_str
        assert "硬件检测报告" in info_str


class TestHardwareDetector:
    """测试硬件检测器."""

    def test_detector_initialization(self):
        """测试检测器初始化."""
        detector = HardwareDetector()

        # 不依赖外部库的情况下应该能正常初始化
        assert detector is not None

    def test_detect_function(self):
        """测试检测功能."""
        detector = HardwareDetector()
        info = detector.detect()

        assert isinstance(info, HardwareInfo)
        assert info.tier in HardwareTier
        assert info.recommended_mode in EngineMode

    def test_global_detect_function(self):
        """测试全局检测函数."""
        info = detect_hardware()

        assert isinstance(info, HardwareInfo)

    def test_check_minimum_requirements(self):
        """测试最低要求检查."""
        meets, message = check_minimum_requirements()

        assert isinstance(meets, bool)
        assert isinstance(message, str)
        assert len(message) > 0


class TestHardwareTier:
    """测试硬件分级枚举."""

    def test_tier_values(self):
        """测试分级值."""
        assert HardwareTier.EXTREME.value == "极限场景"
        assert HardwareTier.BASIC.value == "基础场景"
        assert HardwareTier.PERFORMANCE.value == "性能场景"
        assert HardwareTier.FLAGSHIP.value == "旗舰场景"


class TestEngineMode:
    """测试引擎模式枚举."""

    def test_mode_values(self):
        """测试模式值."""
        assert EngineMode.NATIVE.value == "原生引擎"
        assert EngineMode.HYBRID.value == "混合模式"
        assert EngineMode.EXTERNAL.value == "外部引擎"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
