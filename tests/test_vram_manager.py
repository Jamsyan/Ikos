"""显存管理器测试."""

import pytest

from ikos.core.hardware_detector import HardwareInfo
from ikos.core.vram_manager import MemoryMonitor, Priority, VRAMConfig, VRAMManager, VRAMPool


class TestPriority:
    """测试优先级枚举."""

    def test_priority_values(self):
        """测试优先级值."""
        assert Priority.P0.value == 0
        assert Priority.P1.value == 1
        assert Priority.P2.value == 2
        assert Priority.P3.value == 3


class TestVRAMPool:
    """测试显存池."""

    def test_pool_initialization(self):
        """测试显存池初始化."""
        pool = VRAMPool(total_gb=8.0, reserve_ratio=0.1)

        assert pool.total_gb == 8.0
        assert pool.reserve_ratio == 0.1
        assert pool.reserved_gb == 0.8
        assert pool.available_gb == 7.2

    def test_allocate_success(self):
        """测试分配成功."""
        pool = VRAMPool(total_gb=8.0)

        success = pool.allocate(2.0, "model1")

        assert success is True
        # 可用 = 8.0 * (1 - 0.1) - 2.0 = 5.2
        assert pool.get_available() == pytest.approx(5.2)

    def test_allocate_insufficient_memory(self):
        """测试显存不足."""
        pool = VRAMPool(total_gb=8.0)

        # 尝试分配超过可用显存
        success = pool.allocate(10.0, "model1")

        assert success is False

    def test_allocate_with_priority_preemption(self):
        """测试高优先级抢占."""
        pool = VRAMPool(total_gb=8.0)

        # 先分配低优先级
        pool.allocate(5.0, "model1", Priority.P3)

        # P0 优先级应该能抢占
        success = pool.allocate(5.0, "model2", Priority.P0)

        # 可能成功（如果抢占了 model1）
        assert success is True or "model1" not in pool._allocations

    def test_release(self):
        """测试释放显存."""
        pool = VRAMPool(total_gb=8.0)

        pool.allocate(2.0, "model1")
        pool.release("model1")

        assert pool.get_available() == 7.2  # 回到初始值

    def test_release_nonexistent(self):
        """测试释放不存在的分配."""
        pool = VRAMPool(total_gb=8.0)

        result = pool.release("nonexistent")

        assert result is False

    def test_get_usage(self):
        """测试获取使用情况."""
        pool = VRAMPool(total_gb=8.0)

        pool.allocate(2.0, "model1")
        usage = pool.get_usage()

        assert usage["total_gb"] == 8.0
        assert usage["allocated_gb"] == 2.0
        assert usage["available_gb"] == pytest.approx(5.2)
        assert "usage_percent" in usage

    def test_clear(self):
        """测试清空显存池."""
        pool = VRAMPool(total_gb=8.0)

        pool.allocate(2.0, "model1")
        pool.allocate(3.0, "model2")
        pool.clear()

        assert pool.get_available() == 7.2  # 回到初始值


class TestVRAMConfig:
    """测试显存配置."""

    def test_config_from_hardware(self):
        """测试从硬件创建配置."""
        hardware_info = HardwareInfo(gpu_memory_gb=8.0)

        config = VRAMConfig.from_hardware(hardware_info)

        assert config.total_gb == 8.0
        assert config.reserve_ratio == 0.1
        assert config.enable_monitor is True


class TestVRAMManager:
    """测试显存管理器."""

    def test_manager_initialization(self):
        """测试管理器初始化."""
        config = VRAMConfig(total_gb=8.0)
        manager = VRAMManager(config)

        assert manager is not None
        assert manager.pool is not None

    def test_manager_from_hardware(self):
        """测试从硬件创建管理器."""
        hardware_info = HardwareInfo(gpu_memory_gb=8.0)
        manager = VRAMManager.from_hardware(hardware_info)

        assert manager is not None
        assert manager.config.total_gb == 8.0

    def test_allocate_and_release(self):
        """测试分配和释放."""
        config = VRAMConfig(total_gb=8.0)
        manager = VRAMManager(config)

        success = manager.allocate(2.0, "model1")
        assert success is True

        success = manager.release("model1")
        assert success is True

    def test_get_usage(self):
        """测试获取使用情况."""
        config = VRAMConfig(total_gb=8.0)
        manager = VRAMManager(config)

        manager.allocate(2.0, "model1")
        usage = manager.get_usage()

        assert "total_gb" in usage
        assert "allocated_gb" in usage


class TestMemoryMonitor:
    """测试显存监控器."""

    def test_monitor_initialization(self):
        """测试监控器初始化."""
        monitor = MemoryMonitor()

        assert monitor is not None

    def test_get_gpu_memory_info(self):
        """测试获取显存信息（不依赖实际 GPU）."""
        monitor = MemoryMonitor()

        # 即使没有 GPU 也应该返回 0 而不是报错
        used = monitor.get_gpu_memory_used()
        free = monitor.get_gpu_memory_free()
        total = monitor.get_gpu_memory_total()

        assert isinstance(used, float)
        assert isinstance(free, float)
        assert isinstance(total, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
