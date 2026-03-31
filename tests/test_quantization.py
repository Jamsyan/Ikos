"""量化配置系统测试."""

import pytest

from ikos.core.hardware_detector import HardwareInfo
from ikos.core.quantization_config import (
    QuantizationConfig,
    QuantizationLevel,
    QuantizationLoader,
    QuantizationRecommendation,
    auto_recommend_quantization,
    get_quantization_config,
)


class TestQuantizationLevel:
    """测试量化等级枚举."""

    def test_level_values(self):
        """测试量化等级值."""
        assert QuantizationLevel.NF4.value == "NF4"
        assert QuantizationLevel.INT4.value == "INT4"
        assert QuantizationLevel.INT8.value == "INT8"
        assert QuantizationLevel.FP16.value == "FP16"
        assert QuantizationLevel.FP32.value == "FP32"


class TestQuantizationConfig:
    """测试量化配置类."""

    def test_get_all_configs(self):
        """测试获取所有配置."""
        configs = QuantizationConfig.get_all_configs()

        assert len(configs) == 5

        levels = [c.level for c in configs]
        assert QuantizationLevel.NF4 in levels
        assert QuantizationLevel.INT4 in levels
        assert QuantizationLevel.INT8 in levels
        assert QuantizationLevel.FP16 in levels
        assert QuantizationLevel.FP32 in levels

    def test_memory_calculation(self):
        """测试显存计算."""
        # 7B 模型 FP32 需要 28GB
        config = QuantizationConfig.get_all_configs()[-1]  # FP32
        memory = config.calculate_memory_usage(7.0)
        assert memory == 28.0

        # NF4 量化后应该是 28 * 0.125 = 3.5GB
        nf4_config = QuantizationConfig.get_all_configs()[0]
        memory_nf4 = nf4_config.calculate_memory_usage(7.0)
        assert abs(memory_nf4 - 3.5) < 0.1

    def test_config_str(self):
        """测试配置字符串表示."""
        config = QuantizationConfig.get_all_configs()[0]  # NF4
        config_str = str(config)

        assert "NF4" in config_str
        assert "4bit" in config_str
        assert "显存" in config_str


class TestQuantizationRecommendation:
    """测试量化推荐器."""

    def test_recommendation_initialization(self):
        """测试推荐器初始化."""
        hardware_info = HardwareInfo(gpu_memory_gb=8.0)
        recommender = QuantizationRecommendation(hardware_info)

        assert recommender.hardware_info == hardware_info
        assert recommender.available_memory > 0

    def test_recommend_7b_model(self):
        """测试 7B 模型推荐."""
        # 8GB 显存场景
        hardware_info = HardwareInfo(gpu_memory_gb=8.0)
        recommender = QuantizationRecommendation(hardware_info)

        config = recommender.recommend("qwen3.5:7b")

        # 8GB 显存应该推荐 INT8 或 NF4
        assert config.level in [QuantizationLevel.INT8, QuantizationLevel.NF4]

    def test_recommend_with_extreme_hardware(self):
        """测试极限硬件推荐."""
        # 4GB 显存场景
        hardware_info = HardwareInfo(gpu_memory_gb=4.0)
        recommender = QuantizationRecommendation(hardware_info)

        config = recommender.recommend("qwen3.5:7b")

        # 4GB 显存应该推荐 NF4
        assert config.level == QuantizationLevel.NF4

    def test_recommend_with_flagship_hardware(self):
        """测试旗舰硬件推荐."""
        # 24GB 显存场景
        hardware_info = HardwareInfo(gpu_memory_gb=24.0)
        recommender = QuantizationRecommendation(hardware_info)

        config = recommender.recommend("qwen3.5:7b")

        # 24GB 显存可以推荐 FP16 或 FP32
        assert config.level in [QuantizationLevel.FP16, QuantizationLevel.FP32]

    def test_recommendation_table(self):
        """测试推荐表生成."""
        hardware_info = HardwareInfo(gpu_memory_gb=8.0)
        recommender = QuantizationRecommendation(hardware_info)

        table = recommender.get_recommendation_table("qwen3.5:7b")

        assert isinstance(table, str)
        assert "7B" in table or "7.0" in table
        assert "NF4" in table
        assert "INT8" in table
        assert "FP16" in table


class TestQuantizationLoader:
    """测试量化加载器."""

    def test_get_load_config_nf4(self):
        """测试 NF4 加载配置."""
        config = QuantizationConfig.get_all_configs()[0]  # NF4

        load_config = QuantizationLoader.get_load_config(config, "test_model")

        assert load_config["pretrained_model_name_or_path"] == "test_model"
        assert "load_in_4bit" in load_config or load_config["torch_dtype"] is not None

    def test_get_load_config_fp16(self):
        """测试 FP16 加载配置."""
        config = QuantizationConfig.get_all_configs()[3]  # FP16

        load_config = QuantizationLoader.get_load_config(config, "test_model")

        import torch

        assert load_config["torch_dtype"] == torch.float16


class TestHelperFunctions:
    """测试辅助函数."""

    def test_get_quantization_config(self):
        """测试获取量化配置."""
        config = get_quantization_config("NF4")
        assert config.level == QuantizationLevel.NF4

        config = get_quantization_config("INT8")
        assert config.level == QuantizationLevel.INT8

    def test_get_quantization_config_invalid(self):
        """测试无效量化等级."""
        config = get_quantization_config("INVALID")
        # 应该返回默认的 NF4
        assert config.level == QuantizationLevel.NF4

    def test_auto_recommend_quantization(self):
        """测试自动推荐量化."""
        config = auto_recommend_quantization("qwen3.5:7b")
        assert isinstance(config, QuantizationConfig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
