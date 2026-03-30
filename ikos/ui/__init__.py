"""UI 模块 - 桌面应用界面。

支持两种 UI 模式：
1. QML 模式（推荐）- 现代化界面，支持热重载和 GPU 加速
2. PyQt6 模式（传统）- 纯代码界面，兼容性好
"""

from .main_window_qml import MainWindowQML, run_ui
from .main_window import MainWindow  # 保留旧版兼容

__all__ = ["MainWindowQML", "MainWindow", "run_ui"]
