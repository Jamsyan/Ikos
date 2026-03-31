"""显存管理器 - VRAM 池化管理与监控."""

from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from .hardware_detector import HardwareInfo


class Priority(Enum):
    """任务优先级."""

    P0 = 0  # 最高优先级（可抢占资源）
    P1 = 1  # 高优先级
    P2 = 2  # 普通优先级
    P3 = 3  # 低优先级


@dataclass
class MemoryBlock:
    """显存块."""

    size_gb: float
    priority: Priority
    owner: str
    allocated_at: float = field(default_factory=lambda: 0.0)

    def __hash__(self):
        return hash((self.owner, self.size_gb, self.allocated_at))


class VRAMPool:
    """显存池化管理."""

    def __init__(self, total_gb: float, reserve_ratio: float = 0.1):
        """初始化显存池.

        Args:
            total_gb: 总显存（GB）
            reserve_ratio: 保留比例（默认 10%）
        """
        self.total_gb = total_gb
        self.reserve_ratio = reserve_ratio
        self.available_gb = total_gb * (1 - reserve_ratio)
        self.reserved_gb = total_gb * reserve_ratio

        # 已分配的显存块
        self._allocations: dict[str, MemoryBlock] = {}

        logger.info(f"VRAM 池初始化：总显存 {total_gb:.2f}GB, 可用 {self.available_gb:.2f}GB")

    def allocate(self, size_gb: float, owner: str, priority: Priority = Priority.P2) -> bool:
        """分配显存.

        Args:
            size_gb: 需要分配的显存大小（GB）
            owner: 所有者标识（模型名称）
            priority: 优先级

        Returns:
            bool: 是否分配成功
        """
        # 检查是否已有分配
        if owner in self._allocations:
            logger.warning(f"{owner} 已分配显存，跳过")
            return True

        # 检查显存是否足够
        if size_gb > self.available_gb:
            # 尝试抢占低优先级资源
            if priority == Priority.P0:
                if self._preempt_for_priority(size_gb):
                    logger.info(f"为 {owner} 抢占显存成功")
                else:
                    logger.error(f"无法为 {owner} 抢占足够显存")
                    return False
            else:
                logger.warning(f"显存不足：需要 {size_gb:.2f}GB, 可用 {self.available_gb:.2f}GB")
                return False

        # 分配显存
        import time

        block = MemoryBlock(
            size_gb=size_gb,
            priority=priority,
            owner=owner,
            allocated_at=time.time(),
        )
        self._allocations[owner] = block
        self.available_gb -= size_gb

        logger.info(f"为 {owner} 分配 {size_gb:.2f}GB 显存，剩余 {self.available_gb:.2f}GB")
        return True

    def release(self, owner: str) -> bool:
        """释放显存.

        Args:
            owner: 所有者标识

        Returns:
            bool: 是否释放成功
        """
        if owner not in self._allocations:
            logger.warning(f"{owner} 未分配显存，无法释放")
            return False

        block = self._allocations.pop(owner)
        self.available_gb += block.size_gb

        logger.info(f"释放 {owner} 的 {block.size_gb:.2f}GB 显存，剩余 {self.available_gb:.2f}GB")
        return True

    def get_available(self) -> float:
        """获取可用显存（GB）."""
        return self.available_gb

    def get_total(self) -> float:
        """获取总显存（GB）."""
        return self.total_gb

    def get_usage(self) -> dict:
        """获取显存使用情况."""
        allocated = sum(block.size_gb for block in self._allocations.values())
        return {
            "total_gb": self.total_gb,
            "allocated_gb": allocated,
            "available_gb": self.available_gb,
            "reserved_gb": self.reserved_gb,
            "usage_percent": (allocated / self.total_gb) * 100 if self.total_gb > 0 else 0,
        }

    def _preempt_for_priority(self, needed_gb: float) -> bool:
        """为高优先级任务抢占显存.

        Args:
            needed_gb: 需要的显存大小

        Returns:
            bool: 是否成功抢占
        """
        # 按优先级排序（从低到高）
        sorted_allocs = sorted(
            self._allocations.items(),
            key=lambda x: (x[1].priority.value, x[1].allocated_at),
            reverse=True,
        )

        freed = 0.0
        to_release = []

        for owner, block in sorted_allocs:
            if block.priority == Priority.P0:
                # 不抢占 P0 优先级
                break

            freed += block.size_gb
            to_release.append(owner)

            if freed >= needed_gb:
                break

        if freed >= needed_gb:
            for owner in to_release:
                self.release(owner)
                logger.warning(f"抢占释放 {owner} 的显存")
            return True
        else:
            logger.error(f"无法抢占足够显存：需要 {needed_gb:.2f}GB, 最多可释放 {freed:.2f}GB")
            return False

    def clear(self) -> None:
        """清空所有分配."""
        self._allocations.clear()
        self.available_gb = self.total_gb * (1 - self.reserve_ratio)
        logger.info("VRAM 池已清空")


class MemoryMonitor:
    """显存使用监控."""

    def __init__(self):
        """初始化显存监控器."""
        self._pynvml_available = False
        self._init_pynvml()

    def _init_pynvml(self) -> None:
        """初始化 pynvml."""
        try:
            import pynvml

            self._pynvml = pynvml
            self._pynvml.nvmlInit()
            self._pynvml_available = True
            logger.debug("显存监控器已初始化（pynvml）")
        except ImportError:
            logger.warning("pynvml 不可用，显存监控功能受限")
        except Exception as e:
            logger.error(f"初始化 pynvml 失败：{e}")

    def get_gpu_memory_used(self) -> float:
        """获取已用显存（GB）."""
        if not self._pynvml_available:
            return 0.0

        try:
            handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)
            return memory_info.used / (1024**3)
        except Exception as e:
            logger.error(f"获取已用显存失败：{e}")
            return 0.0

    def get_gpu_memory_free(self) -> float:
        """获取空闲显存（GB）."""
        if not self._pynvml_available:
            return 0.0

        try:
            handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)
            return memory_info.free / (1024**3)
        except Exception as e:
            logger.error(f"获取空闲显存失败：{e}")
            return 0.0

    def get_gpu_memory_total(self) -> float:
        """获取总显存（GB）."""
        if not self._pynvml_available:
            return 0.0

        try:
            handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)
            memory_info = self._pynvml.nvmlDeviceGetMemoryInfo(handle)
            return memory_info.total / (1024**3)
        except Exception as e:
            logger.error(f"获取总显存失败：{e}")
            return 0.0

    def log_usage(self) -> None:
        """记录当前显存使用情况."""
        total = self.get_gpu_memory_total()
        used = self.get_gpu_memory_used()
        free = self.get_gpu_memory_free()

        if total > 0:
            usage_percent = (used / total) * 100
            logger.info(
                f"显存使用：{used:.2f}GB / {total:.2f}GB ({usage_percent:.1f}%), 空闲 {free:.2f}GB"
            )
        else:
            logger.info("显存使用情况 unavailable（pynvml 不可用）")

    def shutdown(self) -> None:
        """关闭监控器."""
        if self._pynvml_available:
            try:
                self._pynvml.nvmlShutdown()
                logger.debug("显存监控器已关闭")
            except Exception as e:
                logger.error(f"关闭 pynvml 失败：{e}")


@dataclass
class VRAMConfig:
    """显存管理配置."""

    # 总显存（GB）
    total_gb: float = 0.0

    # 保留比例（0.1 = 10%）
    reserve_ratio: float = 0.1

    # 是否启用监控
    enable_monitor: bool = True

    # 监控日志间隔（秒）
    log_interval: int = 60

    @classmethod
    def from_hardware(cls, hardware_info: HardwareInfo) -> "VRAMConfig":
        """根据硬件信息创建配置.

        Args:
            hardware_info: 硬件信息

        Returns:
            VRAMConfig: 显存配置
        """
        return cls(
            total_gb=hardware_info.gpu_memory_gb,
            reserve_ratio=0.1,
            enable_monitor=True,
        )


class VRAMManager:
    """显存管理器（统一接口）."""

    def __init__(self, config: VRAMConfig | None = None):
        """初始化显存管理器.

        Args:
            config: 显存配置
        """
        if config is None:
            config = VRAMConfig()

        self.config = config
        self.pool = VRAMPool(total_gb=config.total_gb, reserve_ratio=config.reserve_ratio)
        self.monitor = MemoryMonitor() if config.enable_monitor else None

        logger.info("显存管理器已初始化")

    @classmethod
    def from_hardware(cls, hardware_info: HardwareInfo) -> "VRAMManager":
        """根据硬件信息初始化显存管理器.

        Args:
            hardware_info: 硬件信息

        Returns:
            VRAMManager: 显存管理器
        """
        config = VRAMConfig.from_hardware(hardware_info)
        return cls(config)

    def allocate(self, size_gb: float, owner: str, priority: Priority = Priority.P2) -> bool:
        """分配显存."""
        return self.pool.allocate(size_gb, owner, priority)

    def release(self, owner: str) -> bool:
        """释放显存."""
        return self.pool.release(owner)

    def get_available(self) -> float:
        """获取可用显存."""
        return self.pool.get_available()

    def get_usage(self) -> dict:
        """获取显存使用情况."""
        usage = self.pool.get_usage()

        # 添加实际 GPU 使用情况
        if self.monitor:
            usage["gpu_used"] = self.monitor.get_gpu_memory_used()
            usage["gpu_free"] = self.monitor.get_gpu_memory_free()

        return usage

    def log_usage(self) -> None:
        """记录显存使用情况."""
        if self.monitor:
            self.monitor.log_usage()
        else:
            logger.info(f"VRAM 池使用：{self.pool.get_usage()}")

    def close(self) -> None:
        """关闭管理器."""
        if self.monitor:
            self.monitor.shutdown()
        logger.info("显存管理器已关闭")
