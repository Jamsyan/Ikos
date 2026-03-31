"""硬件检测模块 - 自动检测 GPU、CPU、内存并分级."""

import platform
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger


class HardwareTier(Enum):
    """硬件场景分级."""

    EXTREME = "极限场景"  # 4GB 显存
    BASIC = "基础场景"  # 8GB 显存
    PERFORMANCE = "性能场景"  # 16GB 显存
    FLAGSHIP = "旗舰场景"  # 24GB+ 显存


class EngineMode(Enum):
    """引擎模式."""

    NATIVE = "原生引擎"  # 显存 < 8GB
    HYBRID = "混合模式"  # 显存 8-16GB
    EXTERNAL = "外部引擎"  # 显存 >= 16GB


@dataclass
class HardwareInfo:
    """硬件信息数据类."""

    # GPU 信息
    gpu_model: Optional[str] = None
    gpu_memory_gb: float = 0.0
    gpu_count: int = 0

    # CPU 信息
    cpu_model: str = ""
    cpu_cores: int = 0
    cpu_physical_cores: int = 0

    # 内存信息
    system_memory_gb: float = 0.0
    available_memory_gb: float = 0.0

    # 系统信息
    os_type: str = ""
    python_version: str = ""

    # 分级结果
    tier: HardwareTier = HardwareTier.EXTREME
    recommended_mode: EngineMode = EngineMode.NATIVE

    def __post_init__(self):
        """后处理：根据硬件信息自动分级."""
        self._classify_tier()
        self._recommend_mode()

    def _classify_tier(self) -> None:
        """根据 GPU 显存分级."""
        if self.gpu_memory_gb < 6:
            self.tier = HardwareTier.EXTREME
        elif self.gpu_memory_gb < 12:
            self.tier = HardwareTier.BASIC
        elif self.gpu_memory_gb < 20:
            self.tier = HardwareTier.PERFORMANCE
        else:
            self.tier = HardwareTier.FLAGSHIP

    def _recommend_mode(self) -> None:
        """根据硬件分级推荐引擎模式."""
        if self.tier == HardwareTier.EXTREME:
            self.recommended_mode = EngineMode.NATIVE
        elif self.tier == HardwareTier.BASIC:
            self.recommended_mode = EngineMode.HYBRID
        else:
            self.recommended_mode = EngineMode.EXTERNAL

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "gpu_model": self.gpu_model,
            "gpu_memory_gb": self.gpu_memory_gb,
            "gpu_count": self.gpu_count,
            "cpu_model": self.cpu_model,
            "cpu_cores": self.cpu_cores,
            "cpu_physical_cores": self.cpu_physical_cores,
            "system_memory_gb": self.system_memory_gb,
            "available_memory_gb": self.available_memory_gb,
            "os_type": self.os_type,
            "python_version": self.python_version,
            "tier": self.tier.value,
            "recommended_mode": self.recommended_mode.value,
        }

    def __str__(self) -> str:
        """字符串表示."""
        lines = [
            "=" * 60,
            "硬件检测报告",
            "=" * 60,
            f"GPU: {self.gpu_model or '未检测到独立 GPU'} ({self.gpu_memory_gb:.1f}GB × {self.gpu_count})",
            f"CPU: {self.cpu_model} ({self.cpu_physical_cores} 物理核心 / {self.cpu_cores} 逻辑核心)",
            f"内存：{self.system_memory_gb:.1f}GB (可用：{self.available_memory_gb:.1f}GB)",
            f"系统：{self.os_type}",
            f"硬件分级：{self.tier.value}",
            f"推荐引擎：{self.recommended_mode.value}",
            "=" * 60,
        ]
        return "\n".join(lines)


class HardwareDetector:
    """硬件检测器."""

    def __init__(self):
        """初始化硬件检测器."""
        self._pynvml_available = False
        self._psutil_available = False
        self._init_libraries()

    def _init_libraries(self) -> None:
        """懒加载检测库."""
        try:
            import pynvml

            self._pynvml = pynvml
            self._pynvml_available = True
            logger.debug("pynvml 库已加载，支持 NVIDIA GPU 检测")
        except ImportError:
            logger.warning("pynvml 库未安装，无法检测 NVIDIA GPU 信息")

        try:
            import psutil

            self._psutil = psutil
            self._psutil_available = True
            logger.debug("psutil 库已加载，支持 CPU/内存检测")
        except ImportError:
            logger.warning("psutil 库未安装，无法检测 CPU/内存信息")

    def detect(self) -> HardwareInfo:
        """执行完整硬件检测."""
        logger.info("开始硬件检测...")

        info = HardwareInfo()

        # 检测 GPU
        self._detect_gpu(info)

        # 检测 CPU
        self._detect_cpu(info)

        # 检测内存
        self._detect_memory(info)

        # 检测系统信息
        self._detect_system_info(info)

        logger.info(f"硬件检测完成：{info.tier.value} - {info.recommended_mode.value}")
        return info

    def _detect_gpu(self, info: HardwareInfo) -> None:
        """检测 GPU 信息."""
        if not self._pynvml_available:
            logger.warning("跳过 GPU 检测（pynvml 不可用）")
            return

        try:
            self._pynvml.nvmlInit()
            device_count = self._pynvml.nvmlDeviceGetCount()
            info.gpu_count = device_count

            if device_count > 0:
                # 获取第一个 GPU 信息（主要 GPU）
                handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = self._pynvml.nvmlDeviceGetName(handle)
                memory_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)

                # 解码 GPU 名称（bytes -> str）
                if isinstance(gpu_name, bytes):
                    gpu_name = gpu_name.decode("utf-8")

                info.gpu_model = gpu_name
                info.gpu_memory_gb = memory_info.total / (1024**3)  # 转换为 GB

                logger.info(f"检测到 GPU: {gpu_name} ({info.gpu_memory_gb:.1f}GB)")
            else:
                logger.warning("未检测到 NVIDIA GPU")

            self._pynvml.nvmlShutdown()
        except Exception as e:
            logger.error(f"GPU 检测失败：{e}")

    def _detect_cpu(self, info: HardwareInfo) -> None:
        """检测 CPU 信息."""
        if not self._psutil_available:
            # 使用基础方法检测 CPU
            info.cpu_cores = self._detect_cpu_basic()
            info.cpu_physical_cores = max(1, info.cpu_cores // 2)
            return

        try:
            # CPU 逻辑核心数
            info.cpu_cores = self._psutil.cpu_count(logical=True) or 0

            # CPU 物理核心数
            info.cpu_physical_cores = self._psutil.cpu_count(logical=False) or 0

            # CPU 型号（尝试获取）
            try:
                import platform

                info.cpu_model = platform.processor() or "Unknown CPU"
            except Exception:
                info.cpu_model = "Unknown CPU"

            logger.info(f"检测到 CPU: {info.cpu_physical_cores} 物理核心 / {info.cpu_cores} 逻辑核心")
        except Exception as e:
            logger.error(f"CPU 检测失败：{e}")
            info.cpu_cores = self._detect_cpu_basic()
            info.cpu_physical_cores = max(1, info.cpu_cores // 2)

    def _detect_cpu_basic(self) -> int:
        """基础 CPU 检测方法（不依赖 psutil）."""
        try:
            import os

            return os.cpu_count() or 4
        except Exception:
            return 4

    def _detect_memory(self, info: HardwareInfo) -> None:
        """检测内存信息."""
        if not self._psutil_available:
            # 使用基础方法检测内存
            info.system_memory_gb = self._detect_memory_basic()
            info.available_memory_gb = info.system_memory_gb * 0.5
            return

        try:
            mem = self._psutil.virtual_memory()

            # 总内存（GB）
            info.system_memory_gb = mem.total / (1024**3)

            # 可用内存（GB）
            info.available_memory_gb = mem.available / (1024**3)

            logger.info(f"检测到内存：{info.system_memory_gb:.1f}GB (可用：{info.available_memory_gb:.1f}GB)")
        except Exception as e:
            logger.error(f"内存检测失败：{e}")
            info.system_memory_gb = self._detect_memory_basic()
            info.available_memory_gb = info.system_memory_gb * 0.5

    def _detect_memory_basic(self) -> float:
        """基础内存检测方法（不依赖 psutil）."""
        try:
            import platform

            system = platform.system()

            if system == "Windows":
                # Windows: 使用 ctypes
                import ctypes

                kernel32 = ctypes.windll.kernel32
                c_ulonglong = ctypes.c_ulonglong

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", c_ulonglong),
                        ("ullAvailPhys", c_ulonglong),
                        ("ullTotalPageFile", c_ulonglong),
                        ("ullAvailPageFile", c_ulonglong),
                        ("ullTotalVirtual", c_ulonglong),
                        ("ullAvailVirtual", c_ulonglong),
                        ("ullAvailExtendedVirtual", c_ulonglong),
                    ]

                memory_status = MEMORYSTATUSEX()
                memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))

                return memory_status.ullTotalPhys / (1024**3)
            else:
                # Linux/Mac: 返回默认值
                return 8.0
        except Exception:
            return 8.0

    def _detect_system_info(self, info: HardwareInfo) -> None:
        """检测系统信息."""
        try:
            info.os_type = f"{platform.system()} {platform.release()}"
            info.python_version = platform.python_version()
        except Exception as e:
            logger.error(f"系统信息检测失败：{e}")
            info.os_type = "Unknown"
            info.python_version = "Unknown"

    def get_gpu_memory_info(self) -> dict:
        """获取 GPU 显存详细信息."""
        if not self._pynvml_available:
            return {"total": 0, "used": 0, "free": 0}

        try:
            self._pynvml.nvmlInit()
            handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)

            result = {
                "total": memory_info.total / (1024**3),
                "used": memory_info.used / (1024**3),
                "free": memory_info.free / (1024**3),
            }

            self._pynvml.nvmlShutdown()
            return result
        except Exception as e:
            logger.error(f"获取显存信息失败：{e}")
            return {"total": 0, "used": 0, "free": 0}


# 全局检测器实例（单例模式）
_detector: Optional[HardwareDetector] = None


def detect_hardware() -> HardwareInfo:
    """检测硬件（全局函数）."""
    global _detector
    if _detector is None:
        _detector = HardwareDetector()
    return _detector.detect()


def get_hardware_info() -> HardwareInfo:
    """获取硬件信息（快捷方式）."""
    return detect_hardware()


def check_minimum_requirements() -> tuple[bool, str]:
    """检查是否满足最低运行要求."""
    info = detect_hardware()

    # 最低要求：4GB 显存 或 8GB 内存
    if info.gpu_memory_gb >= 4:
        return True, "满足最低要求（GPU 显存 >= 4GB）"

    if info.system_memory_gb >= 8:
        return True, "满足最低要求（系统内存 >= 8GB，可使用 CPU 推理）"

    return False, "不满足最低要求（需要 4GB 显存或 8GB 系统内存）"
