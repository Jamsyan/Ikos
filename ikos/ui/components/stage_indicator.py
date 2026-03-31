"""阶段指示器 - 可视化展示四阶段执行状态，支持阶段状态显示."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class StageIndicator(QWidget):
    """阶段指示器 - 支持阶段状态显示（未开始/进行中/已完成/失败）."""

    def __init__(self):
        super().__init__()
        self._current_stage = -1
        self._completed_stages = set()
        self._init_ui()

    def _init_ui(self) -> None:
        """初始化 UI."""
        layout = QGridLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        # 四个阶段
        stages = [
            ("1", "需求解析", "解析用户需求，生成知识构建计划"),
            ("2", "智能检索", "多模型拆分搜索，获取海量数据"),
            ("3", "数据筛选", "多模型投票决策，构建知识图谱"),
            ("4", "输出分流", "按配置输出 Markdown/JSON/图谱"),
        ]

        self._stage_widgets = []
        self._num_labels = []
        self._name_labels = []
        self._desc_labels = []

        for i, (num, name, desc) in enumerate(stages):
            stage_widget = self._create_stage_widget(num, name, desc, i)
            row = i // 2
            column = i % 2
            layout.addWidget(stage_widget, row, column)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

    def _create_stage_widget(self, num: str, name: str, desc: str, index: int) -> QWidget:
        """创建阶段组件.

        Args:
            num: 阶段编号
            name: 阶段名称
            desc: 阶段描述
            index: 阶段索引

        Returns:
            QWidget: 阶段组件
        """
        widget = QWidget()
        widget.setMinimumHeight(92)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(widget)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        # 顶部：编号 + 名称
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        # 编号标签
        num_label = QLabel(num)
        num_label.setFixedSize(28, 28)
        num_label.setStyleSheet(self._get_num_style("pending"))
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(num_label)

        # 名称标签
        name_label = QLabel(name)
        name_label.setStyleSheet(self._get_name_style("pending"))
        name_label.setWordWrap(True)
        top_layout.addWidget(name_label)

        layout.addLayout(top_layout)

        # 底部：描述标签
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(self._get_desc_style("pending"))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # 存储引用
        self._stage_widgets.append(widget)
        self._num_labels.append(num_label)
        self._name_labels.append(name_label)
        self._desc_labels.append(desc_label)

        return widget

    def _get_num_style(self, status: str) -> str:
        """获取编号样式.

        Args:
            status: 状态（pending/active/completed/failed）

        Returns:
            str: 样式表
        """
        styles = {
            "pending": """
                QLabel {
                    background-color: #f0f0f0;
                    color: #999999;
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """,
            "active": """
                QLabel {
                    background-color: #1890ff;
                    color: white;
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """,
            "completed": """
                QLabel {
                    background-color: #52c41a;
                    color: white;
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """,
            "failed": """
                QLabel {
                    background-color: #ff4d4f;
                    color: white;
                    border-radius: 14px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """,
        }
        return styles.get(status, styles["pending"])

    def _get_name_style(self, status: str) -> str:
        """获取名称样式.

        Args:
            status: 状态（pending/active/completed/failed）

        Returns:
            str: 样式表
        """
        styles = {
            "pending": """
                QLabel {
                    color: #999999;
                    font-weight: bold;
                    font-size: 13px;
                }
            """,
            "active": """
                QLabel {
                    color: #1890ff;
                    font-weight: bold;
                    font-size: 13px;
                }
            """,
            "completed": """
                QLabel {
                    color: #52c41a;
                    font-weight: bold;
                    font-size: 13px;
                }
            """,
            "failed": """
                QLabel {
                    color: #ff4d4f;
                    font-weight: bold;
                    font-size: 13px;
                }
            """,
        }
        return styles.get(status, styles["pending"])

    def _get_desc_style(self, status: str) -> str:
        """获取描述样式.

        Args:
            status: 状态（pending/active/completed/failed）

        Returns:
            str: 样式表
        """
        styles = {
            "pending": """
                QLabel {
                    color: #bfbfbf;
                    font-size: 11px;
                    line-height: 1.4;
                }
            """,
            "active": """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                    line-height: 1.4;
                }
            """,
            "completed": """
                QLabel {
                    color: #999999;
                    font-size: 11px;
                    line-height: 1.4;
                }
            """,
            "failed": """
                QLabel {
                    color: #ff7875;
                    font-size: 11px;
                    line-height: 1.4;
                }
            """,
        }
        return styles.get(status, styles["pending"])

    def _get_widget_style(self, status: str) -> str:
        """获取组件背景样式.

        Args:
            status: 状态（pending/active/completed/failed）

        Returns:
            str: 样式表
        """
        styles = {
            "pending": "",
            "active": """
                QWidget {
                    background-color: #e6f7ff;
                    border-radius: 8px;
                }
            """,
            "completed": """
                QWidget {
                    background-color: #f6ffed;
                    border-radius: 8px;
                }
            """,
            "failed": """
                QWidget {
                    background-color: #fff1f0;
                    border-radius: 8px;
                }
            """,
        }
        return styles.get(status, "")

    def set_active_stage(self, stage_index: int) -> None:
        """设置激活阶段.

        Args:
            stage_index: 阶段索引（0-3）
        """
        if not hasattr(self, "_stage_widgets"):
            return

        self._current_stage = stage_index

        for i, widget in enumerate(self._stage_widgets):
            if i < stage_index:
                # 已完成的阶段
                status = "completed"
            elif i == stage_index:
                # 当前激活阶段
                status = "active"
            else:
                # 未开始的阶段
                status = "pending"

            # 更新编号样式
            self._num_labels[i].setStyleSheet(self._get_num_style(status))

            # 更新名称样式
            self._name_labels[i].setStyleSheet(self._get_name_style(status))

            # 更新描述样式
            self._desc_labels[i].setStyleSheet(self._get_desc_style(status))

            # 更新背景
            widget.setStyleSheet(self._get_widget_style(status))

    def set_stage_completed(self, stage_index: int) -> None:
        """设置阶段为完成状态.

        Args:
            stage_index: 阶段索引（0-3）
        """
        if not hasattr(self, "_stage_widgets"):
            return
        
        self._completed_stages.add(stage_index)
        
        # 更新该阶段为完成状态
        self._num_labels[stage_index].setStyleSheet(self._get_num_style("completed"))
        self._name_labels[stage_index].setStyleSheet(self._get_name_style("completed"))
        self._desc_labels[stage_index].setStyleSheet(self._get_desc_style("completed"))
        self._stage_widgets[stage_index].setStyleSheet(self._get_widget_style("completed"))

    def set_stage_failed(self, stage_index: int) -> None:
        """设置阶段为失败状态.

        Args:
            stage_index: 阶段索引（0-3）
        """
        if not hasattr(self, "_stage_widgets"):
            return
        
        # 更新该阶段为失败状态
        self._num_labels[stage_index].setStyleSheet(self._get_num_style("failed"))
        self._name_labels[stage_index].setStyleSheet(self._get_name_style("failed"))
        self._desc_labels[stage_index].setStyleSheet(self._get_desc_style("failed"))
        self._stage_widgets[stage_index].setStyleSheet(self._get_widget_style("failed"))

    def reset(self) -> None:
        """重置所有阶段."""
        self._current_stage = -1
        self._completed_stages = set()
        
        if not hasattr(self, "_stage_widgets"):
            return
        
        for i, widget in enumerate(self._stage_widgets):
            # 全部重置为 pending 状态
            self._num_labels[i].setStyleSheet(self._get_num_style("pending"))
            self._name_labels[i].setStyleSheet(self._get_name_style("pending"))
            self._desc_labels[i].setStyleSheet(self._get_desc_style("pending"))
            widget.setStyleSheet(self._get_widget_style("pending"))

    def next_stage(self) -> None:
        """进入下一阶段."""
        if self._current_stage < 0:
            self._current_stage = 0
        else:
            # 将当前阶段标记为完成
            if self._current_stage < len(self._stage_widgets):
                self.set_stage_completed(self._current_stage)
            
            # 进入下一阶段
            self._current_stage = min(self._current_stage + 1, len(self._stage_widgets) - 1)
        
        self.set_active_stage(self._current_stage)

    def get_current_stage(self) -> int:
        """获取当前阶段索引.

        Returns:
            int: 当前阶段索引（-1 表示未开始）
        """
        return self._current_stage

    def get_completed_stages(self) -> set:
        """获取已完成的阶段集合.

        Returns:
            set: 已完成的阶段索引集合
        """
        return self._completed_stages.copy()
