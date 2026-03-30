"""QML 主窗口 - 使用 QML 实现的现代化界面."""

import sys
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, pyqtSignal, QThread
from PyQt6.QtGui import QGuiApplication

from ikos.core.pipeline import IkosPipeline
from .qml_bridge import PythonBridge


class WorkerThread(QThread):
    """工作线程 - 在后台执行管道任务."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, pipeline: IkosPipeline, user_input: str, output_config: dict):
        super().__init__()
        self.pipeline = pipeline
        self.user_input = user_input
        self.output_config = output_config

    def run(self):
        """执行管道任务."""
        try:
            # 执行管道
            result = self.pipeline.run(self.user_input, self.output_config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindowQML(QObject):
    """QML 主窗口控制器。
    
    这个类负责：
    1. 创建和配置 QML 引擎
    2. 提供 Python 后端功能给 QML
    3. 处理业务逻辑
    """

    # ========== 窗口控制信号 ==========
    requestClose = pyqtSignal()

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.engine: Optional[QQmlApplicationEngine] = None
        self.bridge: Optional[PythonBridge] = None
        self.pipeline: Optional[IkosPipeline] = None
        self.worker: Optional[WorkerThread] = None
        
        # 初始化 QML
        self._setup_qml()

    def _setup_qml(self):
        """设置 QML 环境."""
        # 创建桥接对象
        self.bridge = PythonBridge()
        
        # 连接桥接信号到本地槽
        self.bridge.taskStarted.connect(self._on_task_started)
        
        # 创建 QML 引擎
        self.engine = QQmlApplicationEngine()
        
        # 注册 Python 类型为 QML 类型
        qmlRegisterType(PythonBridge, "Ikos", 1, 0, "PythonBridge")
        
        # 导出桥接对象到 QML 上下文
        self.engine.rootContext().setContextProperty("pythonBridge", self.bridge)
        
        # 加载 QML 文件
        qml_file = Path(__file__).parent / "qml" / "Main.qml"
        
        if not qml_file.exists():
            raise FileNotFoundError(f"QML 文件不存在：{qml_file}")
        
        # 启用热重载（开发模式）
        # 设置环境变量后，QML 文件修改会自动重新加载
        os.environ["QML_ENABLE_INSPECTOR"] = "1"
        
        self.engine.load(QUrl.fromLocalFile(str(qml_file)))
        
        if not self.engine.rootObjects():
            raise RuntimeError("无法加载 QML 文件")

    # ========== 槽函数 - 由 QML 调用 ==========
    
    @pyqtSlot(str)
    def startTask(self, user_input: str):
        """开始执行任务。
        
        Args:
            user_input: 用户输入的查询
        """
        if not user_input.strip():
            return
        
        # 发送任务开始信号
        if self.bridge:
            self.bridge.taskStarted.emit()
        
        # 初始化管道（如果需要）
        if self.pipeline is None:
            if self.bridge:
                self.bridge.emit_log("初始化管道...")
            try:
                self.pipeline = IkosPipeline()
                if self.bridge:
                    self.bridge.pipelineInitialized.emit()
            except Exception as e:
                if self.bridge:
                    self.bridge.pipelineInitError.emit(str(e))
                return
        
        # 创建工作线程
        output_config = {"output_type": "file", "formats": ["json", "markdown"]}
        self.worker = WorkerThread(self.pipeline, user_input, output_config)
        
        # 连接信号
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.log.connect(self._on_worker_log)
        
        # 启动线程
        self.worker.start()
        
        if self.bridge:
            self.bridge.emit_log(f"开始处理：{user_input[:50]}...")

    @pyqtSlot()
    def initializePipeline(self):
        """初始化管道。"""
        if self.pipeline is None:
            try:
                self.pipeline = IkosPipeline()
                if self.bridge:
                    self.bridge.pipelineInitialized.emit()
            except Exception as e:
                if self.bridge:
                    self.bridge.pipelineInitError.emit(str(e))

    @pyqtSlot()
    def closeWindow(self):
        """关闭窗口。"""
        self.requestClose.emit()

    # ========== 内部回调方法 ==========
    
    def _on_task_started(self):
        """任务开始回调。"""
        # 这里可以添加额外的逻辑
        pass

    def _on_worker_finished(self, result: dict):
        """工作线程完成回调。
        
        Args:
            result: 任务结果
        """
        if self.bridge:
            self.bridge.emit_task_finished(result)

    def _on_worker_error(self, error: str):
        """工作线程错误回调。
        
        Args:
            error: 错误消息
        """
        if self.bridge:
            self.bridge.emit_task_error(error)

    def _on_worker_log(self, message: str):
        """工作线程日志回调。
        
        Args:
            message: 日志消息
        """
        if self.bridge:
            self.bridge.emit_log(message)

    def cleanup(self):
        """清理资源。"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        if self.engine:
            self.engine.deleteLater()


def run_ui():
    """运行 QML UI 应用。
    
    这是 QML UI 的入口函数。
    """
    from PyQt6.QtCore import Qt
    
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Ikos")
    app.setOrganizationName("Ikos")
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = MainWindowQML(app)
    
    # 连接关闭信号
    window.requestClose.connect(app.quit)
    
    # 运行应用
    sys.exit(app.exec())
