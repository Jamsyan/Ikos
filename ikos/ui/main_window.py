"""主窗口 - 全面重构版 - 知识构建系统定位."""

import sys
from html import escape

from loguru import logger
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog,
                             QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QProgressBar,
                             QPushButton, QScrollArea, QSizePolicy, QSplitter, QTextEdit,
                             QVBoxLayout, QWidget)

from ikos.core import (EngineType, NativeModelLoader, create_native_engine,
                       detect_hardware)
from ikos.core.pipeline import IkosPipeline
from ikos.ui.components import (HardwareMonitorPanel, ModelManagerPanel,
                                StageIndicator)
from ikos.ui.config_manager import UIConfigManager


class WorkerThread(QThread):
    """工作线程."""

    log_signal = pyqtSignal(str, str)
    stage_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, pipeline: IkosPipeline, user_input: str, output_config: dict):
        super().__init__()
        self.pipeline = pipeline
        self.user_input = user_input
        self.output_config = output_config

    @staticmethod
    def _normalize_log_type(level_name: str) -> str:
        level_name = level_name.upper()
        if level_name in {"DEBUG", "INFO"}:
            return "info"
        if level_name == "SUCCESS":
            return "success"
        if level_name == "WARNING":
            return "warning"
        return "error"

    @staticmethod
    def _detect_stage(message: str) -> str | None:
        stage_markers = {
            "第一阶段": "stage1",
            "第二阶段": "stage2",
            "第三阶段": "stage3",
            "第四阶段": "stage4",
        }
        for marker, stage in stage_markers.items():
            if marker in message:
                return stage
        return None

    @staticmethod
    def _rewrite_log_message(message: str) -> str | None:
        if message.startswith("UI 配置已保存"):
            return None

        stage_labels = {
            "=== 第一阶段：需求解析 ===": "进入阶段：需求解析",
            "=== 第二阶段：智能检索 ===": "进入阶段：智能检索",
            "=== 第三阶段：数据筛选 ===": "进入阶段：数据筛选",
            "=== 第四阶段：输出分流 ===": "进入阶段：输出分流",
        }
        if message in stage_labels:
            return stage_labels[message]

        if message.startswith("开始执行流程"):
            return "开始执行构建流程"
        if message == "流程执行完成":
            return "构建流程执行完成"

        return message

    def _forward_log(self, message) -> None:
        record = message.record
        text = record["message"].strip()
        if not text:
            return

        display_text = self._rewrite_log_message(text)
        if not display_text:
            return

        self.log_signal.emit(display_text, self._normalize_log_type(record["level"].name))
        stage = self._detect_stage(text)
        if stage:
            self.stage_signal.emit(stage)

    def run(self):
        sink_id = logger.add(self._forward_log, level="INFO", format="{message}")
        try:
            result = self.pipeline.run(self.user_input, self.output_config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            logger.remove(sink_id)


class MainWindow(QMainWindow):
    """Ikos 主窗口 - 全面重构版."""

    def __init__(self):
        super().__init__()
        self.config_manager = UIConfigManager()
        self.pipeline = None
        self.worker = None
        self.hardware_info = None
        
        self._init_hardware()
        self._init_ui()
        self._load_config()

    def _init_hardware(self) -> None:
        """初始化硬件检测."""
        try:
            self.hardware_info = detect_hardware()
            logger.info(f"硬件检测完成：{self.hardware_info.tier.value}")
        except Exception as e:
            logger.error(f"硬件检测失败：{e}")

    def _init_ui(self) -> None:
        """初始化 UI - 新布局结构."""
        self.setWindowTitle("Ikos - 智能知识构建系统")
        self.setMinimumSize(1200, 820)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 顶部栏
        header = self._create_header()
        layout.addWidget(header)

        # 顶部配置栏
        config_bar = self._create_top_config_bar()
        layout.addWidget(config_bar)

        # 主体内容
        content = QSplitter(Qt.Orientation.Horizontal)
        content.setChildrenCollapsible(False)
        content.setHandleWidth(6)
        content.setStyleSheet("""
            QSplitter::handle {
                background-color: #f0f0f0;
            }
        """)

        left_panel = self._create_left_panel()
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(520)
        content.addWidget(left_panel)

        # 右侧面板
        right_panel = self._create_right_panel()
        content.addWidget(right_panel)
        content.setStretchFactor(0, 3)
        content.setStretchFactor(1, 7)
        content.setSizes([380, 1020])
        self.main_splitter = content

        layout.addWidget(content, 1)

        # 状态栏
        self.statusBar().showMessage("就绪")
        self._set_status("就绪", "#52c41a")

    def _center_window(self) -> None:
        """居中窗口."""
        screen = QApplication.primaryScreen().availableGeometry()
        geometry = self.config_manager.get_window_geometry()
        default_width = min(screen.width() - 80, 1500)
        default_height = min(screen.height() - 80, 980)
        if default_width < 1000:
            default_width = max(screen.width() - 40, 900)
        if default_height < 760:
            default_height = max(screen.height() - 40, 700)

        width = geometry.get("width", default_width)
        height = geometry.get("height", default_height)
        x = geometry.get("x", 100)
        y = geometry.get("y", 100)

        geometry_invalid = (
            width < 1000
            or height < 760
            or x < screen.left()
            or y < screen.top()
            or x + 120 > screen.right()
            or y + 80 > screen.bottom()
        )
        if geometry_invalid:
            width = default_width
            height = default_height
            x = screen.left() + max((screen.width() - width) // 2, 20)
            y = screen.top() + max((screen.height() - height) // 2, 20)
        else:
            width = min(width, screen.width() - 40)
            height = min(height, screen.height() - 40)
            x = min(max(x, screen.left() + 10), screen.right() - width)
            y = min(max(y, screen.top() + 10), screen.bottom() - height)

        self.setGeometry(x, y, width, height)

    def _create_header(self) -> QWidget:
        """顶部栏."""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 2px solid #1890ff;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + 标题
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Ikos")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #1890ff;
            letter-spacing: 1px;
        """)
        
        subtitle = QLabel("Intelligent Knowledge Building System · 智能知识构建系统")
        subtitle.setStyleSheet("font-size: 11px; color: #999999;")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)

        layout.addStretch()

        # 状态
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("""
            QFrame {
                background-color: #52c41a;
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(self.status_dot)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 13px;")
        status_layout.addWidget(self.status_label)

        status_frame = QWidget()
        status_frame.setLayout(status_layout)
        status_frame.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 4px;
                padding: 6px 12px;
            }
        """)
        layout.addWidget(status_frame)

        return header

    def _create_top_config_bar(self) -> QWidget:
        """顶部配置栏 - 横向排列所有配置项."""
        config_widget = QWidget()
        config_widget.setMinimumHeight(110)
        config_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        config_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fafafa, stop:1 #ffffff);
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        layout = QVBoxLayout(config_widget)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        # 配置标题
        title = QLabel("知识构建配置")
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #1890ff;
        """)
        layout.addWidget(title)

        # 配置项横向排列
        config_layout = QHBoxLayout()
        config_layout.setSpacing(20)

        # 模型选择
        model_layout = QVBoxLayout()
        model_label = QLabel("主力模型")
        model_label.setStyleSheet("color: #666666; font-size: 11px;")
        model_layout.addWidget(model_label)
        
        self.model_combo = self._create_combo([
            "Qwen 3.5 7B",
            "Qwen 3.5 14B",
            "DeepSeek-R1 7B",
            "Llama 3.1 8B"
        ])
        self.model_combo.setMinimumWidth(180)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self.model_combo)
        config_layout.addLayout(model_layout)

        # 引擎模式
        engine_layout = QVBoxLayout()
        engine_label = QLabel("引擎模式")
        engine_label.setStyleSheet("color: #666666; font-size: 11px;")
        engine_layout.addWidget(engine_label)
        
        self.engine_combo = self._create_combo([
            "自动",
            "外部引擎",
            "原生引擎",
            "混合模式"
        ])
        self.engine_combo.setMinimumWidth(120)
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self.engine_combo)
        config_layout.addLayout(engine_layout)

        # 量化等级
        quantize_layout = QVBoxLayout()
        quantize_label = QLabel("量化等级")
        quantize_label.setStyleSheet("color: #666666; font-size: 11px;")
        quantize_layout.addWidget(quantize_label)
        
        self.quantize_combo = self._create_combo(["INT4", "INT8", "FP16", "FP32"])
        self.quantize_combo.setMinimumWidth(100)
        self.quantize_combo.currentTextChanged.connect(self._on_quantize_changed)
        quantize_layout.addWidget(self.quantize_combo)
        config_layout.addLayout(quantize_layout)

        config_layout.addSpacing(20)

        # 输出格式
        format_label = QLabel("输出格式")
        format_label.setStyleSheet("color: #666666; font-size: 11px;")
        format_layout = QVBoxLayout()
        format_layout.addWidget(format_label)
        
        format_checkbox_layout = QHBoxLayout()
        format_checkbox_layout.setSpacing(12)
        self.md_check = self._create_check("Markdown", True)
        self.json_check = self._create_check("JSON", True)
        self.graph_check = self._create_check("知识图谱", True)
        for cb in [self.md_check, self.json_check, self.graph_check]:
            format_checkbox_layout.addWidget(cb)
        format_layout.addLayout(format_checkbox_layout)
        config_layout.addLayout(format_layout)

        config_layout.addSpacing(20)

        # 输出目录
        output_dir_layout = QVBoxLayout()
        output_dir_label = QLabel("输出目录")
        output_dir_label.setStyleSheet("color: #666666; font-size: 11px;")
        output_dir_layout.addWidget(output_dir_label)
        
        output_dir_input_layout = QHBoxLayout()
        output_dir_input_layout.setSpacing(5)
        self.output_dir = QLineEdit("./data/output")
        self.output_dir.setMinimumWidth(180)
        self.output_dir.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.output_dir.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 4px 8px;
                color: #333333;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        output_dir_input_layout.addWidget(self.output_dir)
        
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedHeight(32)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #666666;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        browse_btn.clicked.connect(self._browse_output_dir)
        output_dir_input_layout.addWidget(browse_btn)
        output_dir_layout.addLayout(output_dir_input_layout)
        config_layout.addLayout(output_dir_layout)

        config_layout.addStretch()
        layout.addLayout(config_layout)

        return config_widget

    def _create_left_panel(self) -> QWidget:
        """左侧面板 - 任务输入 + 紧凑组件."""
        from PyQt6.QtWidgets import QScrollArea

        panel = QWidget()
        panel.setStyleSheet("background-color: #ffffff;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        scroll.setStyleSheet("border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # 知识构建任务输入
        task_group = self._create_group("知识构建任务")
        task_layout = QVBoxLayout(task_group)
        task_layout.setSpacing(8)

        task_hint = QLabel("请输入知识构建任务，例如：构建量子力学基础概念知识体系")
        task_hint.setStyleSheet("color: #999999; font-size: 11px;")
        task_layout.addWidget(task_hint)

        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText("请详细描述您需要构建的知识领域，包括：\n- 核心主题\n- 关键概念\n- 期望的知识结构\n- 特殊要求...")
        self.task_input.setMinimumHeight(180)
        self.task_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 8px;
                color: #333333;
                font-size: 13px;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QTextEdit:focus {
                border-color: #1890ff;
            }
            QTextEdit::placeholder-text {
                color: #bfbfbf;
            }
        """)
        self.task_input.installEventFilter(self)
        self.task_input.textChanged.connect(self._update_task_char_count)
        task_layout.addWidget(self.task_input)

        # 字符计数
        char_count_layout = QHBoxLayout()
        char_count_layout.addStretch()
        self.char_count_label = QLabel("0 字符")
        self.char_count_label.setStyleSheet("color: #999999; font-size: 10px;")
        char_count_layout.addWidget(self.char_count_label)
        task_layout.addLayout(char_count_layout)

        hint_layout = QHBoxLayout()
        hint_layout.addStretch()
        hint = QLabel("Ctrl+Enter 快速执行")
        hint.setStyleSheet("color: #999999; font-size: 11px;")
        hint_layout.addWidget(hint)
        task_layout.addLayout(hint_layout)

        layout.addWidget(task_group)

        # 硬件监控（紧凑版）
        self.hardware_monitor = HardwareMonitorPanel()
        if hasattr(self, "hardware_info"):
            self.hardware_monitor.set_engine_mode(self.hardware_info.recommended_mode.value)
        self.hardware_monitor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.hardware_monitor)

        # 模型管理（紧凑版）
        self.model_manager = ModelManagerPanel()
        self.model_manager.model_selected.connect(self._on_model_selected)
        self.model_manager.add_predefined_models([
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-3B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        ])
        self.model_manager.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.model_manager)

        # 开始按钮
        self.start_button = QPushButton("开始知识构建")
        self.start_button.setFixedHeight(48)
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1890ff, stop:1 #40a9ff);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #40a9ff, stop:1 #69c0ff);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #096dd9, stop:1 #1890ff);
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d9d9d9, stop:1 #f0f0f0);
                color: #999999;
            }
        """)
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return scroll

    def _create_right_panel(self) -> QWidget:
        """右侧面板 - 流程可视化 + 构建日志."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #fafafa;")
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 构建流程可视化
        workflow_widget = QWidget()
        workflow_widget.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")
        workflow_widget.setMinimumHeight(220)
        
        workflow_layout = QVBoxLayout(workflow_widget)
        workflow_layout.setContentsMargins(20, 15, 20, 15)
        workflow_layout.setSpacing(10)

        workflow_title = QLabel("构建流程")
        workflow_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        workflow_layout.addWidget(workflow_title)

        self.stage_indicator = StageIndicator()
        workflow_layout.addWidget(self.stage_indicator)

        layout.addWidget(workflow_widget)

        # 构建日志
        log_widget = QWidget()
        log_widget.setStyleSheet("background-color: #ffffff;")
        
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(20, 15, 20, 15)
        log_layout.setSpacing(10)

        log_toolbar = QHBoxLayout()
        log_title = QLabel("运行日志")
        log_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        log_toolbar.addWidget(log_title)
        log_toolbar.addStretch()

        # 日志级别过滤
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        filter_label = QLabel("过滤:")
        filter_label.setStyleSheet("color: #666666; font-size: 11px;")
        filter_layout.addWidget(filter_label)
        
        self.filter_info = QCheckBox("INFO")
        self.filter_info.setChecked(True)
        self.filter_info.setStyleSheet("font-size: 11px;")
        self.filter_info.stateChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.filter_info)
        
        self.filter_success = QCheckBox("SUCCESS")
        self.filter_success.setChecked(True)
        self.filter_success.setStyleSheet("font-size: 11px;")
        self.filter_success.stateChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.filter_success)
        
        self.filter_warning = QCheckBox("WARNING")
        self.filter_warning.setChecked(True)
        self.filter_warning.setStyleSheet("font-size: 11px;")
        self.filter_warning.stateChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.filter_warning)
        
        self.filter_error = QCheckBox("ERROR")
        self.filter_error.setChecked(True)
        self.filter_error.setStyleSheet("font-size: 11px;")
        self.filter_error.stateChanged.connect(self._apply_log_filter)
        filter_layout.addWidget(self.filter_error)
        
        log_toolbar.addLayout(filter_layout)

        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.setFixedSize(60, 28)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        export_btn.clicked.connect(self._export_log)
        log_toolbar.addWidget(export_btn)

        clear_btn = QPushButton("清空")
        clear_btn.setFixedSize(60, 28)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
        """)
        clear_btn.clicked.connect(self.clear_log)
        log_toolbar.addWidget(clear_btn)
        log_layout.addLayout(log_toolbar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 8px;
                color: #333333;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background-color: #fafafa;
            }
        """)
        self.log_output.setFont(QFont("Consolas", 11))
        log_layout.addWidget(self.log_output)

        layout.addWidget(log_widget, 1)

        return panel

    def _create_group(self, title: str) -> QGroupBox:
        """创建分组."""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 0;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: #333333;
            }
        """)
        return group

    def _create_label(self, text: str) -> QLabel:
        """创建标签."""
        label = QLabel(text)
        label.setStyleSheet("color: #666666; font-size: 12px;")
        return label

    def _create_combo(self, items: list) -> QComboBox:
        """创建下拉框."""
        combo = QComboBox()
        combo.addItems(items)
        combo.setFixedHeight(32)
        combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                color: #333333;
                font-size: 12px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #999999;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                background-color: white;
                color: #333333;
            }
        """)
        return combo

    def _create_check(self, text: str, checked: bool = False) -> QCheckBox:
        """创建复选框."""
        check = QCheckBox(text)
        check.setChecked(checked)
        check.setStyleSheet("""
            QCheckBox {
                color: #666666;
                font-size: 11px;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid #d9d9d9;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1890ff;
                border-color: #1890ff;
            }
        """)
        return check

    def _browse_output_dir(self) -> None:
        """浏览输出目录."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir.text()
        )
        if dir_path:
            self.output_dir.setText(dir_path)

    def _load_config(self) -> None:
        """加载配置."""
        self._center_window()

        saved_model = self.config_manager.get_model_selection()
        self.model_combo.setCurrentText(saved_model)

        saved_engine = self.config_manager.get_engine_mode()
        self.engine_combo.setCurrentText(saved_engine)

        saved_quantize = self.config_manager.get_quantization_level()
        self.quantize_combo.setCurrentText(saved_quantize)

        output_config = self.config_manager.get_output_config()
        formats = output_config.get("formats", ["markdown", "json"])
        self.md_check.setChecked("markdown" in formats)
        self.json_check.setChecked("json" in formats)
        if "knowledge_graph" in output_config:
            self.graph_check.setChecked(output_config["knowledge_graph"])

        logger.info("UI 配置已恢复")

    def _save_config(self) -> None:
        """保存配置."""
        self.config_manager.set_window_geometry(
            self.x(),
            self.y(),
            self.width(),
            self.height()
        )
        self.config_manager.set_model_selection(self.model_combo.currentText())
        self.config_manager.set_engine_mode(self.engine_combo.currentText())
        self.config_manager.set_quantization_level(self.quantize_combo.currentText())

        formats = []
        if self.md_check.isChecked():
            formats.append("markdown")
        if self.json_check.isChecked():
            formats.append("json")

        self.config_manager.set_output_config({
            "formats": formats,
            "output_dir": self.output_dir.text(),
            "knowledge_graph": self.graph_check.isChecked(),
        })

        logger.info("UI 配置已保存")

    def eventFilter(self, obj, event):
        """事件过滤器."""
        from PyQt6.QtCore import QEvent
        
        if obj == self.task_input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if (key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and
                key_event.modifiers() == Qt.KeyboardModifier.ControlModifier):
                self.start_task()
                return True
        return super().eventFilter(obj, event)

    def _on_model_changed(self, model: str) -> None:
        """模型选择变化."""
        logger.info(f"模型选择：{model}")
        self.config_manager.set_model_selection(model)

    def _update_task_char_count(self) -> None:
        """更新任务字符计数."""
        if hasattr(self, "task_input") and hasattr(self, "char_count_label"):
            text = self.task_input.toPlainText()
            char_count = len(text)
            
            if char_count == 0:
                self.char_count_label.setText("0 字符")
            elif char_count < 100:
                self.char_count_label.setText(f"{char_count} 字符")
            elif char_count < 500:
                self.char_count_label.setText(f"<span style='color: #faad14;'>{char_count} 字符</span>")
            else:
                self.char_count_label.setText(f"<span style='color: #ff4d4f;'>{char_count} 字符</span>")

    def _on_engine_changed(self, engine: str) -> None:
        """引擎模式变化."""
        logger.info(f"引擎模式：{engine}")
        self.config_manager.set_engine_mode(engine)
        
        if hasattr(self, "hardware_monitor"):
            self.hardware_monitor.set_engine_mode(engine)

    def _on_quantize_changed(self, quantize: str) -> None:
        """量化等级变化."""
        logger.info(f"量化等级：{quantize}")
        self.config_manager.set_quantization_level(quantize)

    def _on_model_selected(self, model: str) -> None:
        """模型被选中."""
        if hasattr(self, "model_combo"):
            self.model_combo.setCurrentText(model)
        self._on_model_changed(model)

    def start_task(self):
        """开始任务."""
        task = self.task_input.toPlainText().strip()
        if not task:
            QMessageBox.warning(self, "警告", "请输入知识构建任务")
            return

        self.config_manager.add_recent_query(task)

        self.start_button.setEnabled(False)
        self.start_button.setText("正在构建...")
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.stage_indicator.reset()
        self._set_status("构建进行中", "#1890ff")
        
        self._log_entries = []

        task_preview = task[:50] + ("..." if len(task) > 50 else "")
        self.append_log("已接收构建任务", "info")
        self.append_log(f"任务摘要：{task_preview}", "info")
        self.append_log("正在初始化执行管道", "info")

        try:
            if self.pipeline is None:
                self.pipeline = IkosPipeline()
            self.append_log("执行管道已就绪", "success")
        except Exception as e:
            self.append_log(f"执行管道初始化失败：{e}", "error")
            self.start_button.setEnabled(True)
            self.start_button.setText("开始知识构建")
            self._set_status("初始化失败", "#ff4d4f")
            return

        formats = []
        if self.md_check.isChecked():
            formats.append("markdown")
        if self.json_check.isChecked():
            formats.append("json")

        output_config = {
            "output_type": "file",
            "formats": formats,
            "output_dir": self.output_dir.text(),
            "include_knowledge_graph": self.graph_check.isChecked(),
        }

        self.worker = WorkerThread(self.pipeline, task, output_config)
        self.worker.log_signal.connect(self.append_log)
        self.worker.stage_signal.connect(self.update_stage)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

        self._save_config()

    def append_log(self, message: str, log_type: str = "info"):
        """添加日志."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_type = log_type.lower()
        safe_message = escape(message.strip()).replace("\n", "<br>")

        color_map = {
            "info": "#333333",
            "success": "#52c41a",
            "warning": "#faad14",
            "error": "#ff4d4f",
        }
        color = color_map.get(log_type, "#333333")

        # 存储日志条目（包含类型信息用于过滤）
        if not hasattr(self, "_log_entries"):
            self._log_entries = []
        
        self._log_entries.append({
            "timestamp": timestamp,
            "message": safe_message,
            "raw_message": message.strip(),
            "type": log_type,
            "color": color,
        })

        # 应用过滤后显示
        self._apply_log_filter()

    def _apply_log_filter(self):
        """应用日志过滤器."""
        if not hasattr(self, "_log_entries"):
            return
        
        # 获取选中的过滤条件
        show_info = self.filter_info.isChecked()
        show_success = self.filter_success.isChecked()
        show_warning = self.filter_warning.isChecked()
        show_error = self.filter_error.isChecked()
        
        # 清空当前显示
        self.log_output.clear()
        
        # 根据过滤条件重新显示
        for entry in self._log_entries:
            log_type = entry["type"]
            
            # 检查是否应该显示
            should_show = False
            if log_type == "info" and show_info:
                should_show = True
            elif log_type == "success" and show_success:
                should_show = True
            elif log_type == "warning" and show_warning:
                should_show = True
            elif log_type == "error" and show_error:
                should_show = True
            
            if should_show:
                self.log_output.append(
                    f'<span style="color: #999999;">[{entry["timestamp"]}]</span> '
                    f'<span style="color: {entry["color"]};">{entry["message"]}</span>'
                )

    def _export_log(self):
        """导出日志到文件."""
        from PyQt6.QtWidgets import QFileDialog
        
        if not hasattr(self, "_log_entries") or not self._log_entries:
            QMessageBox.information(self, "提示", "没有可导出的日志")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            "ikos_log.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for entry in self._log_entries:
                        f.write(f"[{entry['timestamp']}] [{entry['type'].upper()}] {entry['raw_message']}\n")
                
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"日志已导出到:\n{file_path}"
                )
                logger.info(f"日志已导出到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出日志失败:\n{e}")
                logger.error(f"导出日志失败：{e}")

    def clear_log(self):
        """清空日志."""
        if hasattr(self, "_log_entries"):
            self._log_entries = []
        self.log_output.clear()

    def update_stage(self, stage: str):
        """更新阶段."""
        stage_map = {
            "stage1": 0,
            "stage2": 1,
            "stage3": 2,
            "stage4": 3,
        }
        stage_index = stage_map.get(stage, 0)
        self.stage_indicator.set_active_stage(stage_index)

        progress_map = {"stage1": 20, "stage2": 40, "stage3": 60, "stage4": 80}
        self.progress_bar.setValue(progress_map.get(stage, 0))
        stage_status = {
            "stage1": "需求解析中",
            "stage2": "智能检索中",
            "stage3": "数据筛选中",
            "stage4": "输出整理中",
        }
        self._set_status(stage_status.get(stage, "构建进行中"), "#1890ff")

    def on_task_finished(self, result: dict):
        """任务完成."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始知识构建")
        self.progress_bar.setValue(100)

        if result.get("status") == "success":
            self.stage_indicator.set_stage_completed(3)
            self.append_log("知识构建完成", "success")
            if result.get("output_files"):
                self.append_log("输出文件列表", "info")
                for file_info in result["output_files"]:
                    self.append_log(
                        f"{file_info.get('filename', 'unknown')} -> {file_info.get('path', 'unknown')}",
                        "info"
                    )
            
            # 更新状态栏显示输出文件数量
            file_count = len(result.get("output_files", []))
            self._set_status(f"构建完成，已生成 {file_count} 个文件", "#52c41a")
        else:
            self.append_log(f"知识构建失败：{result.get('error', 'unknown')}", "error")
            self._set_status("构建失败", "#ff4d4f")

        self._save_config()

    def on_task_error(self, error_msg: str):
        """任务错误."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始知识构建")
        self.progress_bar.setValue(0)
        self._set_status("构建失败", "#ff4d4f")
        self.append_log(f"执行错误：{error_msg}", "error")

    def _set_status(self, text: str, color: str) -> None:
        """统一更新顶部状态与状态栏。"""
        self.status_label.setText(text)
        self.statusBar().showMessage(text)
        self.status_dot.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)

    def closeEvent(self, event):
        """窗口关闭."""
        self._save_config()
        
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        if hasattr(self, "hardware_monitor"):
            self.hardware_monitor.stop_monitoring()
        
        if hasattr(self, "model_manager"):
            self.model_manager.stop_download()
        
        event.accept()


def run_ui():
    """运行 UI."""
    from loguru import logger
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
