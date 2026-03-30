"""UI 模块 - 桌面应用界面。

提供 PyQt6 桌面应用界面：
- 主窗口
- 任务面板
- 配置面板
- 进度展示
"""

from .main_window import MainWindow
from .task_panel import TaskPanel
from .config_panel import ConfigPanel

__all__ = [
    "MainWindow",
    "TaskPanel",
    "ConfigPanel",
]
