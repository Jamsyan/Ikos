"""主窗口 - 使用 QWidget 实现的专业深色主题 UI."""

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
    QSplitter,
    QFrame,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ikos.core.pipeline import IkosPipeline


# ========== 专业深色主题配色方案 ==========
# 基于 Material Design 3 和现代 IDE 配色
# 参考：VS Code Dark+, GitHub Dark, One Dark Pro

class Theme:
    """专业深色主题配色."""
    
    # 背景色 - 使用深灰而非纯黑
    BG_PRIMARY = "#18181b"      # 主背景（最暗）
    BG_SECONDARY = "#1e1e2e"    # 次级背景（卡片）
    BG_TERTIARY = "#252537"     # 第三级背景（输入框）
    BG_HOVER = "#2a2a3f"        # 悬停背景
    
    # 强调色 - 降低饱和度，避免发光
    PRIMARY = "#7aa2f7"         # 主色调（柔和蓝）
    PRIMARY_HOVER = "#5d87e5"   # 悬停色
    ACCENT = "#bb9af7"          # 点缀色（紫色）
    
    # 语义色 - 降低饱和度
    SUCCESS = "#9ece6a"         # 成功（柔和绿）
    WARNING = "#e0af68"         # 警告（柔和黄）
    ERROR = "#f7768e"           # 错误（柔和红）
    INFO = "#7dcfff"            # 信息（柔和青）
    
    # 文本色 - 高对比度
    TEXT_PRIMARY = "#c0caf5"    # 主文本
    TEXT_SECONDARY = "#a9b1d6"  # 次要文本
    TEXT_MUTED = "#565f89"      # 弱化文本
    TEXT_WHITE = "#ffffff"      # 纯白（特殊用途）
    
    # 边框色
    BORDER = "#414868"          # 主边框
    BORDER_LIGHT = "#565f89"    # 亮边框


class WorkerThread(QThread):
    """工作线程 - 后台执行管道任务."""

    log_signal = pyqtSignal(str, str)
    stage_signal = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, pipeline: IkosPipeline, user_input: str, output_config: dict):
        super().__init__()
        self.pipeline = pipeline
        self.user_input = user_input
        self.output_config = output_config

    def run(self):
        """执行管道任务."""
        try:
            result = self.pipeline.run(self.user_input, self.output_config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Ikos 主窗口 - 专业深色主题."""

    def __init__(self):
        super().__init__()
        self.pipeline = None
        self.worker = None
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """初始化用户界面."""
        self.setWindowTitle("Ikos - 智能知识构建系统 v0.1.1")
        self.setGeometry(100, 100, 1400, 900)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 20, 25, 20)

        # ===== 顶部栏 =====
        header = self.create_header()
        main_layout.addWidget(header)

        # ===== 主工作区 =====
        work_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        work_splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        work_splitter.addWidget(right_panel)
        
        work_splitter.setStretchFactor(0, 1)
        work_splitter.setStretchFactor(1, 2)
        work_splitter.setSizes([400, 1000])
        
        main_layout.addWidget(work_splitter)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def create_header(self) -> QFrame:
        """创建顶部栏."""
        header = QFrame()
        header.setMinimumHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Logo
        logo = QLabel("I")
        logo.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                color: {Theme.TEXT_WHITE};
                font-size: 20px;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px;
                min-width: 36px;
                min-height: 36px;
            }}
        """)
        layout.addWidget(logo)

        # 标题
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title = QLabel("Ikos")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        subtitle = QLabel("Intelligent Knowledge Building System")
        subtitle.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        layout.addStretch()

        # 状态指示器
        self.status_indicator = QFrame()
        self.status_indicator.setMinimumSize(8, 8)
        self.status_indicator.setMaximumSize(8, 8)
        self.status_indicator.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SUCCESS};
                border-radius: 4px;
            }}
        """)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        
        status_frame = QFrame()
        status_frame.setLayout(status_layout)
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 6px 12px;
            }}
        """)
        
        layout.addWidget(status_frame)

        return header

    def create_left_panel(self) -> QWidget:
        """创建左侧配置面板."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # 模型配置
        model_group = self.create_group("模型配置")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(10)

        model_layout.addWidget(self.create_label("主力模型"))
        self.model_combo = self.create_combo([
            "Qwen 3.5 7B", "Qwen 3.5 14B", 
            "DeepSeek-R1 7B", "Llama 3.1 8B"
        ])
        model_layout.addWidget(self.model_combo)

        model_layout.addWidget(self.create_label("引擎模式"))
        self.engine_combo = self.create_combo([
            "自动", "外部引擎", "原生引擎", "混合模式"
        ])
        model_layout.addWidget(self.engine_combo)

        model_layout.addWidget(self.create_label("量化等级"))
        self.quantize_combo = self.create_combo([
            "INT4", "INT8", "FP16", "FP32"
        ])
        model_layout.addWidget(self.quantize_combo)

        layout.addWidget(model_group)

        # 输出配置
        output_group = self.create_group("输出配置")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(10)

        output_layout.addWidget(self.create_label("输出格式"))
        format_layout = QHBoxLayout()
        self.md_check = self.create_check("Markdown", True)
        self.json_check = self.create_check("JSON", True)
        self.graph_check = self.create_check("知识图谱", True)
        for cb in [self.md_check, self.json_check, self.graph_check]:
            format_layout.addWidget(cb)
        output_layout.addLayout(format_layout)

        output_layout.addWidget(self.create_label("输出目录"))
        self.output_dir = QLineEdit("./data/output")
        self.output_dir.setStyleSheet(self.input_style())
        output_layout.addWidget(self.output_dir)

        layout.addWidget(output_group)

        # 开始按钮
        self.start_button = QPushButton("开始执行任务")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                color: {Theme.TEXT_WHITE};
                font-size: 15px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.PRIMARY_HOVER}, stop:1 #a384e5);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a6dcf, stop:1 #8f74d4);
            }}
            QPushButton:disabled {{
                background: {Theme.BORDER};
                color: {Theme.TEXT_MUTED};
            }}
        """)
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_TERTIARY};
                border: none;
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # 查询输入
        query_group = self.create_group("查询输入")
        query_layout = QVBoxLayout(query_group)
        query_layout.setSpacing(10)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText(
            "请输入你的查询，例如：量子力学基础概念、傅里叶变换的数学原理..."
        )
        self.query_input.setMinimumHeight(100)
        self.query_input.setMaximumHeight(140)
        self.query_input.setStyleSheet(self.textedit_style())
        self.query_input.installEventFilter(self)
        query_layout.addWidget(self.query_input)

        hint = QLabel("Ctrl+Enter 快速执行")
        hint.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 11px;")
        query_layout.addWidget(hint)

        layout.addWidget(query_group)

        # 执行日志
        log_group = self.create_group("执行日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(10)

        # 工具栏
        toolbar = QHBoxLayout()
        clear_btn = QPushButton("清空")
        clear_btn.setMaximumWidth(60)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ERROR};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #e0657a;
            }}
        """)
        clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(clear_btn)
        toolbar.addStretch()
        log_layout.addLayout(toolbar)

        # 日志区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {Theme.TEXT_PRIMARY};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.5;
            }}
        """)
        self.log_output.setFont(QFont("Consolas", 11))
        log_layout.addWidget(self.log_output)

        layout.addWidget(log_group)
        return panel

    # ========== 辅助方法 ==========

    def create_group(self, title: str) -> QGroupBox:
        """创建分组框."""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                font-size: 13px;
                font-weight: bold;
                color: {Theme.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        return group

    def create_label(self, text: str) -> QLabel:
        """创建标签."""
        label = QLabel(text)
        label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        return label

    def create_combo(self, items: list) -> QComboBox:
        """创建下拉框."""
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(self.combo_style())
        return combo

    def create_check(self, text: str, checked: bool = False) -> QCheckBox:
        """创建复选框."""
        check = QCheckBox(text)
        check.setChecked(checked)
        check.setStyleSheet(f"""
            QCheckBox {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 12px;
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {Theme.BORDER};
                background-color: {Theme.BG_TERTIARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.PRIMARY};
                border-color: {Theme.PRIMARY};
            }}
        """)
        return check

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理 Ctrl+Enter."""
        from PyQt6.QtCore import QEvent
        
        if obj == self.query_input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if (key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and
                key_event.modifiers() == Qt.KeyboardModifier.ControlModifier):
                self.start_task()
                return True
        return super().eventFilter(obj, event)

    def start_task(self):
        """开始执行任务."""
        query = self.query_input.toPlainText().strip()
        if not query:
            return

        self.start_button.setEnabled(False)
        self.start_button.setText("执行中...")
        self.progress_bar.setValue(0)
        self.log_output.clear()

        self.append_log(f"开始任务：{query[:50]}...", "info")
        self.append_log("初始化管道...", "info")

        try:
            if self.pipeline is None:
                self.pipeline = IkosPipeline()
            self.append_log("管道初始化完成", "success")
        except Exception as e:
            self.append_log(f"管道初始化失败：{e}", "error")
            self.start_button.setEnabled(True)
            self.start_button.setText("开始执行任务")
            return

        formats = []
        if self.md_check.isChecked():
            formats.append("markdown")
        if self.json_check.isChecked():
            formats.append("json")

        output_config = {
            "output_type": "file",
            "formats": formats,
            "output_dir": self.output_dir.text()
        }

        self.worker = WorkerThread(self.pipeline, query, output_config)
        self.worker.log_signal.connect(self.append_log)
        self.worker.stage_signal.connect(self.update_stage)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

        self.statusBar().showMessage("任务执行中...")

    def append_log(self, message: str, log_type: str = "info"):
        """添加日志."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        color_map = {
            "info": Theme.INFO,
            "success": Theme.SUCCESS,
            "warning": Theme.WARNING,
            "error": Theme.ERROR,
        }
        color = color_map.get(log_type, Theme.TEXT_PRIMARY)

        self.log_output.append(
            f'<span style="color: {Theme.TEXT_MUTED};">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )

    def clear_log(self):
        """清空日志."""
        self.log_output.clear()

    def update_stage(self, stage: str):
        """更新阶段."""
        stage_names = {
            "stage1": "阶段 1: 需求解析",
            "stage2": "阶段 2: 智能检索",
            "stage3": "阶段 3: 数据筛选",
            "stage4": "阶段 4: 输出分流",
        }
        stage_name = stage_names.get(stage, stage)
        self.append_log(stage_name, "info")

        progress_map = {
            "stage1": 20,
            "stage2": 40,
            "stage3": 60,
            "stage4": 80,
        }
        self.progress_bar.setValue(progress_map.get(stage, 0))

    def on_task_finished(self, result: dict):
        """任务完成回调."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始执行任务")
        self.progress_bar.setValue(100)
        self.statusBar().showMessage("任务完成")

        if result.get("status") == "success":
            self.append_log("\n✅ 任务执行成功", "success")
            if result.get("output_files"):
                self.append_log("\n输出文件:", "info")
                for file_info in result["output_files"]:
                    self.append_log(
                        f"  - {file_info.get('filename', 'unknown')} "
                        f"({file_info.get('path', 'unknown')})",
                        "info"
                    )
        else:
            self.append_log(
                f"\n❌ 任务执行失败：{result.get('error', 'unknown error')}",
                "error"
            )

    def on_task_error(self, error_msg: str):
        """任务错误回调."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始执行任务")
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("任务失败")
        self.append_log(f"\n❌ 错误：{error_msg}", "error")

    def closeEvent(self, event):
        """窗口关闭事件."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()

    # ========== 样式方法 ==========

    def apply_theme(self):
        """应用全局主题."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {Theme.BG_PRIMARY};
            }}
            QFrame {{
                background-color: transparent;
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

    def combo_style(self) -> str:
        """下拉框样式."""
        return f"""
            QComboBox {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
                min-height: 36px;
            }}
            QComboBox:hover {{
                border-color: {Theme.BORDER_LIGHT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {Theme.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.BG_SECONDARY};
                border: 1px solid {Theme.BORDER};
                selection-background-color: {Theme.BORDER};
                color: {Theme.TEXT_PRIMARY};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                height: 36px;
                padding: 0 8px;
            }}
            QComboBox::disabled {{
                background-color: {Theme.BG_HOVER};
                color: {Theme.TEXT_MUTED};
            }}
        """

    def input_style(self) -> str:
        """输入框样式."""
        return f"""
            QLineEdit {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                color: {Theme.TEXT_PRIMARY};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.BORDER_LIGHT};
            }}
        """

    def textedit_style(self) -> str:
        """文本编辑框样式."""
        return f"""
            QTextEdit {{
                background-color: {Theme.BG_TERTIARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                padding: 12px;
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QTextEdit:focus {{
                border-color: {Theme.BORDER_LIGHT};
            }}
            QTextEdit::placeholder-text {{
                color: {Theme.TEXT_MUTED};
            }}
        """


def run_ui():
    """运行 UI 应用."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
