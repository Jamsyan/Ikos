"""主窗口 - 完整重构版."""

import sys
from loguru import logger
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
    QFrame,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ikos.core.pipeline import IkosPipeline
from ikos.core import (
    detect_hardware,
    create_native_engine,
    EngineType,
    NativeModelLoader,
)
from ikos.ui.config_manager import UIConfigManager
from ikos.ui.components import HardwareMonitorPanel, ModelManagerPanel, StageIndicator


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

    def run(self):
        try:
            result = self.pipeline.run(self.user_input, self.output_config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Ikos 主窗口 - 完整重构版."""

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
        """初始化 UI."""
        self.setWindowTitle("Ikos - 智能知识构建系统")
        self._center_window()

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 顶部栏
        header = self._create_header()
        layout.addWidget(header)

        # 主体内容
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧面板（350px）
        left_panel = self._create_left_panel()
        left_panel.setFixedWidth(350)
        content_layout.addWidget(left_panel)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedWidth(1)
        content_layout.addWidget(separator)

        # 右侧面板
        right_panel = self._create_right_panel()
        content_layout.addWidget(right_panel)

        layout.addWidget(content)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def _center_window(self) -> None:
        """居中窗口."""
        screen = QApplication.primaryScreen().geometry()
        
        # 使用保存的配置或默认值
        geometry = self.config_manager.get_window_geometry()
        
        # 如果保存的位置超出屏幕，使用居中
        if geometry["x"] + geometry["width"] > screen.width():
            # 屏幕的 80% 宽度，75% 高度
            window_width = int(screen.width() * 0.8)
            window_height = int(screen.height() * 0.75)
            x = (screen.width() - window_width) // 2
            y = (screen.height() - window_height) // 2
            self.setGeometry(x, y, window_width, window_height)
        else:
            self.setGeometry(
                geometry["x"],
                geometry["y"],
                geometry["width"],
                geometry["height"]
            )

    def _create_header(self) -> QWidget:
        """顶部栏."""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Logo + 标题
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel("Ikos")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333333;")
        
        subtitle = QLabel("Intelligent Knowledge Building System")
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

    def _create_left_panel(self) -> QWidget:
        """左侧面板."""
        from PyQt6.QtWidgets import QScrollArea

        panel = QWidget()
        panel.setStyleSheet("background-color: #ffffff;")
        
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        scroll.setStyleSheet("border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 硬件监控
        self.hardware_monitor = HardwareMonitorPanel()
        if hasattr(self, "hardware_info"):
            self.hardware_monitor.set_engine_mode(self.hardware_info.recommended_mode.value)
        layout.addWidget(self.hardware_monitor)

        # 模型管理
        self.model_manager = ModelManagerPanel()
        self.model_manager.model_selected.connect(self._on_model_selected)
        self.model_manager.add_predefined_models([
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-3B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        ])
        layout.addWidget(self.model_manager)

        # 模型配置
        model_group = self._create_group("模型配置")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(12)

        model_layout.addWidget(self._create_label("主力模型"))
        self.model_combo = self._create_combo([
            "Qwen 3.5 7B",
            "Qwen 3.5 14B",
            "DeepSeek-R1 7B",
            "Llama 3.1 8B"
        ])
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self.model_combo)

        model_layout.addWidget(self._create_label("引擎模式"))
        self.engine_combo = self._create_combo([
            "自动",
            "外部引擎",
            "原生引擎",
            "混合模式"
        ])
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)
        model_layout.addWidget(self.engine_combo)

        model_layout.addWidget(self._create_label("量化等级"))
        self.quantize_combo = self._create_combo(["INT4", "INT8", "FP16", "FP32"])
        self.quantize_combo.currentTextChanged.connect(self._on_quantize_changed)
        model_layout.addWidget(self.quantize_combo)

        layout.addWidget(model_group)

        # 输出配置
        output_group = self._create_group("输出配置")
        output_layout = QVBoxLayout(output_group)
        output_layout.setSpacing(12)

        output_layout.addWidget(self._create_label("输出格式"))
        format_layout = QHBoxLayout()
        format_layout.setSpacing(15)
        self.md_check = self._create_check("Markdown", True)
        self.json_check = self._create_check("JSON", True)
        self.graph_check = self._create_check("知识图谱", True)
        for cb in [self.md_check, self.json_check, self.graph_check]:
            format_layout.addWidget(cb)
        output_layout.addLayout(format_layout)

        output_layout.addWidget(self._create_label("输出目录"))
        self.output_dir = QLineEdit("./data/output")
        self.output_dir.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 6px 10px;
                color: #333333;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        output_layout.addWidget(self.output_dir)

        layout.addWidget(output_group)

        # 开始按钮
        self.start_button = QPushButton("开始执行任务")
        self.start_button.setFixedHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #999999;
            }
        """)
        self.start_button.clicked.connect(self.start_task)
        layout.addWidget(self.start_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return scroll

    def _create_right_panel(self) -> QWidget:
        """右侧面板."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #fafafa;")
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 查询输入
        query_widget = QWidget()
        query_widget.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")
        query_widget.setFixedHeight(200)
        
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(20, 15, 20, 15)
        query_layout.setSpacing(10)

        query_title = QLabel("查询输入")
        query_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        query_layout.addWidget(query_title)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("请输入你的查询，例如：量子力学基础概念、傅里叶变换的数学原理...")
        self.query_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 8px;
                color: #333333;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #1890ff;
            }
            QTextEdit::placeholder-text {
                color: #bfbfbf;
            }
        """)
        self.query_input.installEventFilter(self)
        query_layout.addWidget(self.query_input)

        hint = QLabel("Ctrl+Enter 快速执行")
        hint.setStyleSheet("color: #999999; font-size: 11px;")
        query_layout.addWidget(hint)

        layout.addWidget(query_widget)

        # 阶段指示器
        stage_widget = QWidget()
        stage_widget.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")
        stage_widget.setFixedHeight(80)
        
        stage_layout = QVBoxLayout(stage_widget)
        stage_layout.setContentsMargins(20, 15, 20, 15)
        stage_layout.setSpacing(10)

        stage_title = QLabel("执行阶段")
        stage_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        stage_layout.addWidget(stage_title)

        self.stage_indicator = StageIndicator()
        stage_layout.addWidget(self.stage_indicator)

        layout.addWidget(stage_widget)

        # 执行日志
        log_widget = QWidget()
        log_widget.setStyleSheet("background-color: #ffffff;")
        
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(20, 15, 20, 15)
        log_layout.setSpacing(10)

        log_toolbar = QHBoxLayout()
        log_title = QLabel("执行日志")
        log_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333;")
        log_toolbar.addWidget(log_title)
        log_toolbar.addStretch()

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
                font-family: 'Consolas', monospace;
                font-size: 12px;
                background-color: #fafafa;
            }
        """)
        self.log_output.setFont(QFont("Consolas", 11))
        log_layout.addWidget(self.log_output)

        layout.addWidget(log_widget)

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
        combo.setFixedHeight(36)
        combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                color: #333333;
                font-size: 13px;
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
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
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

    def _load_config(self) -> None:
        """加载配置."""
        # 恢复窗口几何
        geometry = self.config_manager.get_window_geometry()
        self.setGeometry(
            geometry["x"],
            geometry["y"],
            geometry["width"],
            geometry["height"]
        )

        # 恢复模型选择
        saved_model = self.config_manager.get_model_selection()
        self.model_combo.setCurrentText(saved_model)

        # 恢复引擎模式
        saved_engine = self.config_manager.get_engine_mode()
        self.engine_combo.setCurrentText(saved_engine)

        # 恢复量化等级
        saved_quantize = self.config_manager.get_quantization_level()
        self.quantize_combo.setCurrentText(saved_quantize)

        # 恢复输出配置
        output_config = self.config_manager.get_output_config()
        formats = output_config.get("formats", ["markdown", "json"])
        self.md_check.setChecked("markdown" in formats)
        self.json_check.setChecked("json" in formats)

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
            "include_knowledge_graph": self.graph_check.isChecked(),
        })

        logger.info("UI 配置已保存")

    def eventFilter(self, obj, event):
        """事件过滤器."""
        from PyQt6.QtCore import QEvent
        
        if obj == self.query_input and event.type() == QEvent.Type.KeyPress:
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
        self.model_combo.setCurrentText(model)
        self._on_model_changed(model)

    def start_task(self):
        """开始任务."""
        query = self.query_input.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入查询内容")
            return

        # 保存最近的查询
        self.config_manager.add_recent_query(query)

        self.start_button.setEnabled(False)
        self.start_button.setText("执行中...")
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.stage_indicator.reset()

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
            "output_dir": self.output_dir.text(),
            "include_knowledge_graph": self.graph_check.isChecked(),
        }

        self.worker = WorkerThread(self.pipeline, query, output_config)
        self.worker.log_signal.connect(self.append_log)
        self.worker.stage_signal.connect(self.update_stage)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

        self.statusBar().showMessage("任务执行中...")
        self._save_config()

    def append_log(self, message: str, log_type: str = "info"):
        """添加日志."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        color_map = {
            "info": "#333333",
            "success": "#52c41a",
            "warning": "#faad14",
            "error": "#ff4d4f",
        }
        color = color_map.get(log_type, "#333333")

        self.log_output.append(
            f'<span style="color: #999999;">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )

    def clear_log(self):
        """清空日志."""
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

        stage_names = {
            "stage1": "阶段 1: 需求解析",
            "stage2": "阶段 2: 智能检索",
            "stage3": "阶段 3: 数据筛选",
            "stage4": "阶段 4: 输出分流",
        }
        self.append_log(stage_names.get(stage, stage), "info")

    def on_task_finished(self, result: dict):
        """任务完成."""
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
            self.append_log(f"\n❌ 任务执行失败：{result.get('error', 'unknown')}", "error")

        self._save_config()

    def on_task_error(self, error_msg: str):
        """任务错误."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始执行任务")
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("任务失败")
        self.append_log(f"\n❌ 错误：{error_msg}", "error")

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
