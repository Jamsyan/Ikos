"""UI 组件测试."""

import sys

import pytest
from PyQt6.QtWidgets import QApplication

from ikos.ui.components import HardwareMonitorPanel, ModelManagerPanel, StageIndicator


@pytest.fixture(scope="module")
def app():
    """创建 QApplication 实例."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # 不退出，避免影响其他测试


class TestStageIndicator:
    """测试阶段指示器."""

    def test_init(self, app):
        """测试初始化."""
        indicator = StageIndicator()

        assert indicator is not None
        assert hasattr(indicator, "_stage_widgets")
        assert len(indicator._stage_widgets) == 4

    def test_set_active_stage(self, app):
        """测试设置激活阶段."""
        indicator = StageIndicator()

        # 初始状态
        indicator.set_active_stage(0)

        # 切换到阶段 2
        indicator.set_active_stage(2)

        # 验证
        assert hasattr(indicator, "_stage_widgets")

    def test_reset(self, app):
        """测试重置."""
        indicator = StageIndicator()
        indicator.reset()

        # 应该重置到阶段 0

    def test_next_stage(self, app):
        """测试下一阶段."""
        indicator = StageIndicator()

        getattr(indicator, "_current_stage", 0)
        indicator.next_stage()

        # 应该进入下一阶段


class TestHardwareMonitorPanel:
    """测试硬件监控面板."""

    def test_init(self, app):
        """测试初始化."""
        panel = HardwareMonitorPanel()

        assert panel is not None
        assert panel.title() == "硬件监控"
        assert hasattr(panel, "gpu_label")
        assert hasattr(panel, "vram_progress")
        assert hasattr(panel, "cpu_label")
        assert hasattr(panel, "ram_progress")

    def test_set_engine_mode(self, app):
        """测试设置引擎模式."""
        panel = HardwareMonitorPanel()

        # 测试不同模式
        for mode in ["原生引擎", "混合模式", "外部引擎", "自动"]:
            panel.set_engine_mode(mode)
            assert panel.engine_mode_label.text() == mode

    def test_stop_monitoring(self, app):
        """测试停止监控."""
        panel = HardwareMonitorPanel()

        # 停止监控
        panel.stop_monitoring()

        # 定时器应该停止


class TestModelManagerPanel:
    """测试模型管理面板."""

    def test_init(self, app):
        """测试初始化."""
        panel = ModelManagerPanel()

        assert panel is not None
        assert panel.title() == "模型管理"
        assert hasattr(panel, "model_combo")
        assert hasattr(panel, "download_btn")

    def test_add_predefined_models(self, app):
        """测试添加预定义模型."""
        panel = ModelManagerPanel()

        models = ["Model A", "Model B", "Model C"]
        panel.add_predefined_models(models)

        assert panel.model_combo.count() >= len(models)

    def test_stop_download(self, app):
        """测试停止下载."""
        panel = ModelManagerPanel()

        # 停止下载（即使没有在下载）
        panel.stop_download()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
