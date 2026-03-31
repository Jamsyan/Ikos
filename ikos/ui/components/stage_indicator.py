"""阶段指示器 - 可视化展示四阶段执行状态."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StageIndicator(QWidget):
    """阶段指示器."""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化 UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 10, 0, 10)

        # 四个阶段
        self.stage_labels = []
        stages = [
            ("1", "需求解析"),
            ("2", "智能检索"),
            ("3", "数据筛选"),
            ("4", "输出分流"),
        ]

        for i, (num, name) in enumerate(stages):
            stage_widget = self._create_stage_widget(num, name, i == 0)
            layout.addWidget(stage_widget)

            # 添加箭头（除了最后一个）
            if i < len(stages) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #999999; font-size: 16px; font-weight: bold;")
                layout.addWidget(arrow)

        layout.addStretch()

    def _create_stage_widget(self, num: str, name: str, active: bool = False) -> QWidget:
        """创建阶段组件.

        Args:
            num: 阶段编号
            name: 阶段名称
            active: 是否激活

        Returns:
            QWidget: 阶段组件
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 8, 12, 8)

        # 编号标签
        num_label = QLabel(num)
        num_label.setFixedSize(24, 24)
        num_label.setStyleSheet(self._get_num_style(active))
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(num_label)

        # 名称标签
        name_label = QLabel(name)
        name_label.setStyleSheet(self._get_name_style(active))
        layout.addWidget(name_label)

        # 存储引用以便后续更新
        if not hasattr(self, "_stage_widgets"):
            self._stage_widgets = []
            self._num_labels = []
            self._name_labels = []

        self._stage_widgets.append(widget)
        self._num_labels.append(num_label)
        self._name_labels.append(name_label)

        return widget

    def _get_num_style(self, active: bool) -> str:
        """获取编号样式.

        Args:
            active: 是否激活

        Returns:
            str: 样式表
        """
        if active:
            return """
                QLabel {
                    background-color: #1890ff;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
        else:
            return """
                QLabel {
                    background-color: #f0f0f0;
                    color: #999999;
                    border-radius: 12px;
                    font-size: 13px;
                }
            """

    def _get_name_style(self, active: bool) -> str:
        """获取名称样式.

        Args:
            active: 是否激活

        Returns:
            str: 样式表
        """
        if active:
            return """
                QLabel {
                    color: #1890ff;
                    font-weight: bold;
                    font-size: 13px;
                }
            """
        else:
            return """
                QLabel {
                    color: #999999;
                    font-size: 13px;
                }
            """

    def set_active_stage(self, stage_index: int) -> None:
        """设置激活阶段.

        Args:
            stage_index: 阶段索引（0-3）
        """
        if not hasattr(self, "_stage_widgets"):
            return

        for i, widget in enumerate(self._stage_widgets):
            is_active = (i == stage_index)

            # 更新编号样式
            self._num_labels[i].setStyleSheet(self._get_num_style(is_active))

            # 更新名称样式
            self._name_labels[i].setStyleSheet(self._get_name_style(is_active))

            # 更新背景
            if is_active:
                widget.setStyleSheet("""
                    QWidget {
                        background-color: #e6f7ff;
                        border-radius: 6px;
                    }
                """)
            else:
                widget.setStyleSheet("")

    def reset(self) -> None:
        """重置所有阶段."""
        self.set_active_stage(0)

    def next_stage(self) -> None:
        """进入下一阶段."""
        if hasattr(self, "_current_stage"):
            self._current_stage = min(self._current_stage + 1, 3)
        else:
            self._current_stage = 0
        self.set_active_stage(self._current_stage)
