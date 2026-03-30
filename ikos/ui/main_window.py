"""主窗口 - PyQt6 桌面应用主界面."""

import sys
from PyQt6.QtWidgets import (
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
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from ikos.core.pipeline import IkosPipeline


class WorkerThread(QThread):
    """工作线程 - 在后台执行管道任务."""

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
    """Ikos 主窗口."""

    def __init__(self):
        super().__init__()
        self.pipeline = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """初始化用户界面."""
        self.setWindowTitle("Ikos - 智能知识构建系统")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("Ikos - Intelligent Knowledge Building System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 上部：输入区域
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)

        input_label = QLabel("输入查询：")
        input_layout.addWidget(input_label)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("例如：量子力学基础概念、傅里叶变换的数学原理...")
        self.input_edit.returnPressed.connect(self.start_task)
        input_layout.addWidget(self.input_edit)

        self.start_button = QPushButton("开始执行")
        self.start_button.clicked.connect(self.start_task)
        input_layout.addWidget(self.start_button)

        splitter.addWidget(input_frame)

        # 下部：输出区域
        output_frame = QFrame()
        output_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        output_layout = QVBoxLayout(output_frame)

        output_label = QLabel("输出日志：")
        output_layout.addWidget(output_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        output_layout.addWidget(self.output_text)

        splitter.addWidget(output_frame)

        # 设置分割器初始比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def start_task(self):
        """开始执行任务."""
        user_input = self.input_edit.text().strip()
        if not user_input:
            return

        # 禁用按钮
        self.start_button.setEnabled(False)
        self.start_button.setText("执行中...")
        self.output_text.clear()

        # 初始化管道
        if self.pipeline is None:
            self.output_text.append("初始化管道...")
            try:
                self.pipeline = IkosPipeline()
                self.output_text.append("管道初始化完成")
            except Exception as e:
                self.output_text.append(f"管道初始化失败：{e}")
                self.start_button.setEnabled(True)
                self.start_button.setText("开始执行")
                return

        # 创建工作线程
        output_config = {"output_type": "file", "formats": ["json", "markdown"]}
        self.worker = WorkerThread(self.pipeline, user_input, output_config)
        self.worker.finished.connect(self.on_task_finished)
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

        self.statusBar().showMessage("任务执行中...")

    def on_task_finished(self, result):
        """任务完成回调."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始执行")
        self.statusBar().showMessage("任务完成")

        if result.get("status") == "success":
            self.output_text.append("\n✅ 任务执行成功")
            if result.get("output_files"):
                self.output_text.append("\n输出文件:")
                for file_info in result["output_files"]:
                    self.output_text.append(
                        f"  - {file_info.get('filename', 'unknown')} "
                        f"({file_info.get('path', 'unknown')})"
                    )
        else:
            self.output_text.append(f"\n❌ 任务执行失败：{result.get('error', 'unknown error')}")

    def on_task_error(self, error_msg):
        """任务错误回调."""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始执行")
        self.statusBar().showMessage("任务失败")
        self.output_text.append(f"\n❌ 错误：{error_msg}")

    def closeEvent(self, event):
        """窗口关闭事件."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()


def run_ui():
    """运行 UI 应用."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


# 需要在这里导入 QApplication，避免循环导入
from PyQt6.QtWidgets import QApplication
