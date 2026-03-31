"""量化配置系统 - 支持多精度量化等级与自动推荐."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger

from .hardware_detector import HardwareInfo, HardwareTier


class QuantizationLevel(Enum):
    """量化等级."""

    NF4 = "NF4"  # 4bit Normal Float（推荐）
    INT4 = "INT4"  # 4bit Integer
    INT8 = "INT8"  # 8bit Integer
    FP16 = "FP16"  # 16bit Float
    FP32 = "FP32"  # 32bit Float


@dataclass
class QuantizationConfig:
    """量化配置."""

    # 量化等级
    level: QuantizationLevel

    # 精度（bit）
    bits: int

    # 显存占用比例（相对于 FP32）
    memory_ratio: float

    # 质量损失预估（%）
    quality_loss_percent: float

    # 是否推荐用于极限场景
    recommended_for_extreme: bool = False

    # 是否推荐用于基础场景
    recommended_for_basic: bool = False

    # 是否推荐用于性能场景
    recommended_for_performance: bool = False

    # 是否推荐用于旗舰场景
    recommended_for_flagship: bool = False

    @classmethod
    def get_all_configs(cls) -> list["QuantizationConfig"]:
        """获取所有预定义的量化配置."""
        return [
            cls(
                level=QuantizationLevel.NF4,
                bits=4,
                memory_ratio=0.125,
                quality_loss_percent=5.0,
                recommended_for_extreme=True,
            ),
            cls(
                level=QuantizationLevel.INT4,
                bits=4,
                memory_ratio=0.125,
                quality_loss_percent=7.0,
                recommended_for_extreme=True,
            ),
            cls(
                level=QuantizationLevel.INT8,
                bits=8,
                memory_ratio=0.25,
                quality_loss_percent=3.0,
                recommended_for_basic=True,
            ),
            cls(
                level=QuantizationLevel.FP16,
                bits=16,
                memory_ratio=0.5,
                quality_loss_percent=1.0,
                recommended_for_performance=True,
            ),
            cls(
                level=QuantizationLevel.FP32,
                bits=32,
                memory_ratio=1.0,
                quality_loss_percent=0.0,
                recommended_for_flagship=True,
            ),
        ]

    def calculate_memory_usage(self, model_params_billions: float) -> float:
        """计算模型显存占用（GB）.

        Args:
            model_params_billions: 模型参数量（十亿）

        Returns:
            float: 显存占用（GB）
        """
        # FP32 基准：每个参数 4 bytes
        fp32_memory = model_params_billions * 4  # GB

        # 根据量化等级计算
        return fp32_memory * self.memory_ratio

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "level": self.level.value,
            "bits": self.bits,
            "memory_ratio": self.memory_ratio,
            "quality_loss_percent": self.quality_loss_percent,
            "recommended_for_extreme": self.recommended_for_extreme,
            "recommended_for_basic": self.recommended_for_basic,
            "recommended_for_performance": self.recommended_for_performance,
            "recommended_for_flagship": self.recommended_for_flagship,
        }

    def __str__(self) -> str:
        """字符串表示."""
        return (
            f"{self.level.value} ({self.bits}bit) - "
            f"显存：{self.memory_ratio * 100:.0f}%, "
            f"质量损失：{self.quality_loss_percent:.1f}%"
        )


class QuantizationRecommendation:
    """量化推荐器."""

    # 模型参数量与 FP32 显存占用对照表
    MODEL_MEMORY_TABLE = {
        "0.5B": 2.0,  # 0.5B 参数 FP32 需要 2GB
        "1B": 4.0,
        "2B": 8.0,
        "3B": 12.0,
        "4B": 16.0,
        "7B": 28.0,
        "9B": 36.0,
        "14B": 56.0,
        "35B": 140.0,
        "70B": 280.0,
    }

    def __init__(self, hardware_info: HardwareInfo):
        """初始化推荐器.

        Args:
            hardware_info: 硬件信息
        """
        self.hardware_info = hardware_info
        self.available_memory = self._calculate_available_memory()

    def _calculate_available_memory(self) -> float:
        """计算可用显存（考虑保留比例）."""
        # 保留 10% 显存
        if self.hardware_info.gpu_memory_gb > 0:
            return self.hardware_info.gpu_memory_gb * 0.9
        else:
            # 无 GPU，使用系统内存
            return self.hardware_info.system_memory_gb * 0.8

    def recommend(self, model_name: str) -> QuantizationConfig:
        """为指定模型推荐量化等级.

        Args:
            model_name: 模型名称（如 "qwen3.5:7b"）

        Returns:
            QuantizationConfig: 推荐的量化配置
        """
        # 提取模型参数量
        model_size = self._extract_model_size(model_name)

        if not model_size:
            # 无法提取，返回默认推荐
            logger.warning(f"无法从模型名称提取参数量：{model_name}，使用默认推荐")
            return self._default_recommendation()

        # 获取模型 FP32 显存占用
        fp32_memory = self.MODEL_MEMORY_TABLE.get(model_size, 0.0)

        if fp32_memory == 0:
            logger.warning(f"未知模型大小：{model_size}，使用默认推荐")
            return self._default_recommendation()

        # 根据可用显存推荐
        return self._recommend_by_memory(fp32_memory)

    def _extract_model_size(self, model_name: str) -> Optional[str]:
        """从模型名称提取参数量.

        Args:
            model_name: 模型名称

        Returns:
            Optional[str]: 参数量标识（如 "7B"）
        """
        import re

        # 匹配模式：qwen3.5:7b, deepseek-r1:14b, llama3.1:8b
        match = re.search(r":?(\d+(?:\.\d+)?)[bB]$", model_name)
        if match:
            size = match.group(1)
            # 标准化格式
            if "." in size:
                return f"{size}B"
            else:
                return f"{size}B"

        return None

    def _recommend_by_memory(self, fp32_memory: float) -> QuantizationConfig:
        """根据显存需求推荐量化等级.

        Args:
            fp32_memory: FP32 显存占用（GB）

        Returns:
            QuantizationConfig: 推荐的量化配置
        """
        configs = QuantizationConfig.get_all_configs()

        # 按显存占用排序（从小到大）
        sorted_configs = sorted(configs, key=lambda c: c.memory_ratio)

        for config in sorted_configs:
            required_memory = fp32_memory * config.memory_ratio

            if required_memory <= self.available_memory:
                logger.info(
                    f"推荐量化：{config.level.value} - "
                    f"需要 {required_memory:.2f}GB, 可用 {self.available_memory:.2f}GB"
                )
                return config

        # 所有量化都超出，返回最小的
        logger.warning(f"显存不足，即使 NF4 量化也需要 {fp32_memory * 0.125:.2f}GB")
        return configs[0]  # 返回 NF4

    def _default_recommendation(self) -> QuantizationConfig:
        """默认推荐（根据硬件分级）."""
        tier = self.hardware_info.tier

        if tier == HardwareTier.EXTREME:
            return self._get_config(QuantizationLevel.NF4)
        elif tier == HardwareTier.BASIC:
            return self._get_config(QuantizationLevel.INT8)
        elif tier == HardwareTier.PERFORMANCE:
            return self._get_config(QuantizationLevel.FP16)
        else:
            return self._get_config(QuantizationLevel.FP32)

    def _get_config(self, level: QuantizationLevel) -> QuantizationConfig:
        """获取指定量化等级的配置."""
        configs = QuantizationConfig.get_all_configs()
        for config in configs:
            if config.level == level:
                return config

        # 找不到，返回 NF4
        return configs[0]

    def get_recommendation_table(self, model_name: str) -> str:
        """生成推荐表（字符串格式）.

        Args:
            model_name: 模型名称

        Returns:
            str: 推荐表字符串
        """
        model_size = self._extract_model_size(model_name)
        if not model_size:
            return "无法提取模型参数量"

        fp32_memory = self.MODEL_MEMORY_TABLE.get(model_size, 0.0)
        if fp32_memory == 0:
            return f"未知模型大小：{model_size}"

        lines = [
            f"模型：{model_name} (FP32: {fp32_memory:.1f}GB)",
            f"可用显存：{self.available_memory:.1f}GB",
            "",
            "量化方案对比:",
            "-" * 60,
            f"{'量化等级':<10} {'显存占用':<12} {'质量损失':<10} {'推荐':<8}",
            "-" * 60,
        ]

        configs = QuantizationConfig.get_all_configs()
        recommended = self.recommend(model_name)

        for config in configs:
            memory = fp32_memory * config.memory_ratio
            loss = f"{config.quality_loss_percent:.0f}%"
            mark = "✅" if config == recommended else ""

            lines.append(f"{config.level.value:<10} {memory:>6.1f}GB{'':<5} {loss:<10} {mark:<8}")

        lines.append("-" * 60)
        lines.append(f"推荐：{recommended.level.value}")

        return "\n".join(lines)


class QuantizationLoader:
    """量化加载配置生成器."""

    @staticmethod
    def get_load_config(config: QuantizationConfig, model_path: str) -> dict:
        """获取模型加载配置.

        Args:
            config: 量化配置
            model_path: 模型路径

        Returns:
            dict: 加载配置（用于 transformers.AutoModelForCausalLM.from_pretrained）
        """
        import torch

        base_config = {
            "pretrained_model_name_or_path": model_path,
            "torch_dtype": torch.float32,
            "device_map": "auto",
            "low_cpu_mem_usage": True,
        }

        if config.level in [QuantizationLevel.NF4, QuantizationLevel.INT4]:
            # 4bit 量化加载
            try:
                import bitsandbytes as bnb

                base_config["load_in_4bit"] = True
                base_config["bnb_4bit_compute_dtype"] = torch.float16
                base_config["bnb_4bit_use_double_quant"] = True
                base_config["bnb_4bit_quant_type"] = (
                    "nf4" if config.level == QuantizationLevel.NF4 else "int4"
                )

                logger.info(f"配置 4bit 量化加载：{config.level.value}")
            except ImportError:
                logger.warning("bitsandbytes 未安装，降级为 INT8 量化")
                return QuantizationLoader.get_load_config(
                    QuantizationConfig.get_all_configs()[2],  # INT8
                    model_path,
                )

        elif config.level == QuantizationLevel.INT8:
            # 8bit 量化加载
            try:
                import bitsandbytes as bnb

                base_config["load_in_8bit"] = True
                logger.info("配置 8bit 量化加载")
            except ImportError:
                logger.warning("bitsandbytes 未安装，降级为 FP16")
                return QuantizationLoader.get_load_config(
                    QuantizationConfig.get_all_configs()[3],  # FP16
                    model_path,
                )

        elif config.level == QuantizationLevel.FP16:
            # FP16 精度
            base_config["torch_dtype"] = torch.float16
            logger.info("配置 FP16 精度加载")

        elif config.level == QuantizationLevel.FP32:
            # FP32 精度（默认）
            logger.info("配置 FP32 精度加载")

        return base_config


def auto_recommend_quantization(
    model_name: str,
    hardware_info: Optional[HardwareInfo] = None,
) -> QuantizationConfig:
    """自动推荐量化等级（全局函数）.

    Args:
        model_name: 模型名称
        hardware_info: 硬件信息（可选，自动检测）

    Returns:
        QuantizationConfig: 推荐的量化配置
    """
    from .hardware_detector import detect_hardware

    if hardware_info is None:
        hardware_info = detect_hardware()

    recommender = QuantizationRecommendation(hardware_info)
    return recommender.recommend(model_name)


def get_quantization_config(level: str) -> QuantizationConfig:
    """获取量化配置（全局函数）.

    Args:
        level: 量化等级字符串（NF4/INT4/INT8/FP16/FP32）

    Returns:
        QuantizationConfig: 量化配置
    """
    configs = QuantizationConfig.get_all_configs()
    level_upper = level.upper()

    for config in configs:
        if config.level.value == level_upper:
            return config

    # 找不到，返回默认
    logger.warning(f"未知量化等级：{level}，使用默认 NF4")
    return configs[0]
