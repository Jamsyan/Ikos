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
    QGridLayout,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QBrush

from ikos.core.pipeline import IkosPipeline


class WorkerThread(QThread):
    """工作线程 - 后台执行管道任务."""

    log_signal = pyqtSignal(str, str)  # message, type
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
        self.apply_dark_theme()

    def init_ui(self):
        """初始化用户界面."""
        self.setWindowTitle("Ikos - 智能知识构建系统 v0.1.1")
        self.setGeometry(100, 100, 1400, 900)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===== 顶部栏：Logo + 标题 + 状态 =====
        header_frame = self.create_header()
        main_layout.addWidget(header_frame)

        # ===== 主工作区 =====
        work_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：配置面板
        left_panel = self.create_config_panel()
        work_splitter.addWidget(left_panel)

        # 右侧：查询和日志
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
        header.setFrameStyle(QFrame.Shape.StyledPanel)
        header.setMinimumHeight(70)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # Logo
        logo_label = QLabel("I")
        logo_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #06b6d4);
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 10px;
                padding: 10px;
                min-width: 40px;
                min-height: 40px;
                alignment: center;
            }
        """)
        layout.addWidget(logo_label)

        # 标题
        title_layout = QVBoxLayout()
        title_label = QLabel("Ikos")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #f1f5f9;")
        subtitle_label = QLabel("Intelligent Knowledge Building System")
        subtitle_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        layout.addStretch()

        # 状态指示器
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                padding: 5px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setSpacing(8)

        status_indicator = QFrame()
        status_indicator.setMinimumSize(8, 8)
        status_indicator.setMaximumSize(8, 8)
        status_indicator.setStyleSheet("""
            QFrame {
                background-color: #10b981;
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(status_indicator)

        status_text = QLabel("就绪")
        status_text.setStyleSheet("color: #94a3b8; font-size: 12px;")
        status_layout.addWidget(status_text)

        layout.addWidget(status_frame)

        return header

    def create_config_panel(self) -> QWidget:
        """创建左侧配置面板."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # 模型配置
        model_group = QGroupBox("模型配置")
        model_group.setStyleSheet(self.group_style())
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(10)

        # 主力模型
        model_layout.addWidget(QLabel("主力模型"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Qwen 3.5 7B",
            "Qwen 3.5 14B",
            "DeepSeek-R1 7B",
            "Llama 3.1 8B"
        ])
        self.model_combo.setStyleSheet(self.combo_style())
        model_layout.addWidget(self.model_combo)

        # 引擎模式
        model_layout.addWidget(QLabel("引擎模式"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["自动", "外部引擎", "原生引擎", "混合模式"])
        self.engine_combo.setStyleSheet(self.combo_style())
        model_layout.addWidget(self.engine_combo)

        # 量化等级
        model_layout.addWidget(QLabel("量化等级"))
        self.quantize_combo = QComboBox()
        self.quantize_combo.addItems(["INT4", "INT8", "FP16", "FP32"])
        self.quantize_combo.setStyleSheet(self.combo_style())
        model_layout.addWidget(self.quantize_combo)

        layout.addWidget(model_group)

        # 输出配置
        output_group = QGroupBox("输出配置")
        output_group.setStyleSheet(self.group_style())
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(10)

        # 输出格式
        output_layout.addWidget(QLabel("输出格式"))
        format_layout = QHBoxLayout()
        self.md_check = QCheckBox("Markdown")
        self.json_check = QCheckBox("JSON")
        self.graph_check = QCheckBox("知识图谱")
        self.md_check.setChecked(True)
        self.json_check.setChecked(True)
        self.graph_check.setChecked(True)
        for cb in [self.md_check, self.json_check, self.graph_check]:
            cb.setStyleSheet("color: #94a3b8;")
            format_layout.addWidget(cb)
        output_layout.addLayout(format_layout)

        # 输出目录
        output_layout.addWidget(QLabel("输出目录"))
        self.output_dir = QLineEdit("./data/output")
        self.output_dir.setStyleSheet(self.input_style())
        output_layout.addWidget(self.output_dir)

        layout.addWidget(output_group)

        # 开始按钮
        self.start_button = QPushButton("开始执行任务")
        self.start_button.setMinimumHeight(60)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #06b6d4);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4f46e5, stop:1 #0891b2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4338ca, stop:1 #0e7490);
            }
            QPushButton:disabled {
                background: #505050;
                color: #808080;
            }
        """)
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a2e;
                border: none;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #06b6d4);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板（查询 + 日志）."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # 查询输入
        query_group = QGroupBox("查询输入")
        query_group.setStyleSheet(self.group_style())
        query_layout = QVBoxLayout(query_group)
        query_layout.setSpacing(10)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText(
            "请输入你的查询，例如：量子力学基础概念、傅里叶变换的数学原理..."
        )
        self.query_input.setMinimumHeight(100)
        self.query_input.setMaximumHeight(150)
        self.query_input.setStyleSheet(self.textedit_style())
        self.query_input.installEventFilter(self)
        query_layout.addWidget(self.query_input)

        hint_label = QLabel("Ctrl+Enter 快速执行")
        hint_label.setStyleSheet("color: #64748b; font-size: 11px;")
        query_layout.addWidget(hint_label)

        layout.addWidget(query_group)

        # 执行日志
        log_group = QGroupBox("执行日志")
        log_group.setStyleSheet(self.group_style())
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(10)

        # 日志工具栏
        log_toolbar = QHBoxLayout()
        clear_button = QPushButton("清空")
        clear_button.setMaximumWidth(70)
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        clear_button.clicked.connect(self.clear_log)
        log_toolbar.addWidget(clear_button)
        log_toolbar.addStretch()
        log_layout.addLayout(log_toolbar)

        # 日志区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(self.log_style())
        self.log_output.setFont(QFont("Consolas", 11))
        log_layout.addWidget(self.log_output)

        layout.addWidget(log_group)

        return panel

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理 Ctrl+Enter."""
        from PyQt6.QtGui import QKeyEvent
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

        # 更新 UI 状态
        self.start_button.setEnabled(False)
        self.start_button.setText("执行中...")
        self.progress_bar.setValue(0)
        self.log_output.clear()

        # 添加日志
        self.append_log(f"开始任务：{query[:50]}...", "info")
        self.append_log("初始化管道...", "info")

        # 初始化管道
        try:
            if self.pipeline is None:
                self.pipeline = IkosPipeline()
            self.append_log("管道初始化完成", "success")
        except Exception as e:
            self.append_log(f"管道初始化失败：{e}", "error")
            self.start_button.setEnabled(True)
            self.start_button.setText("开始执行任务")
            return

        # 创建工作线程
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
            "info": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
        }
        color = color_map.get(log_type, "#f1f5f9")

        self.log_output.append(
            f'<span style="color: #64748b;">[{timestamp}]</span> '
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

    def apply_dark_theme(self):
        """应用全局深色主题."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f0f1a;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #f1f5f9;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #f1f5f9;
            }
        """)

    def group_style(self) -> str:
        """分组框样式."""
        return """
            QGroupBox {
                background-color: rgba(37, 37, 66, 0.95);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #f1f5f9;
                font-size: 14px;
                font-weight: bold;
            }
        """

    def combo_style(self) -> str:
        """下拉框样式."""
        return """
            QComboBox {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: #f1f5f9;
                font-size: 13px;
            }
            QComboBox:hover {
                border-color: rgba(99, 102, 241, 0.3);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #94a3b8;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                selection-background-color: rgba(99, 102, 241, 0.3);
                color: #f1f5f9;
            }
        """

    def input_style(self) -> str:
        """输入框样式."""
        return """
            QLineEdit {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: #f1f5f9;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: rgba(99, 102, 241, 0.5);
            }
        """

    def textedit_style(self) -> str:
        """文本编辑框样式."""
        return """
            QTextEdit {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #f1f5f9;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: rgba(99, 102, 241, 0.5);
            }
            QTextEdit::placeholder-text {
                color: #64748b;
            }
        """

    def log_style(self) -> str:
        """日志框样式."""
        return """
            QTextEdit {
                background-color: #1a1a2e;
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-radius: 8px;
                padding: 12px;
                color: #f1f5f9;
                font-family: Consolas, monospace;
            }
        """


def run_ui():
    """运行 UI 应用."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
