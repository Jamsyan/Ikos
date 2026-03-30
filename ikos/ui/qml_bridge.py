"""Python-QML 桥接类 - 实现 Python 与 QML 之间的通信."""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Optional, Any


class PythonBridge(QObject):
    """Python 与 QML 之间的桥接类。
    
    这个类作为 Python 后端和 QML 前端之间的桥梁，
    允许 QML 调用 Python 方法，并接收 Python 的信号。
    """

    # ========== 发送到 QML 的信号 ==========
    
    # 任务状态信号
    taskStarted = pyqtSignal()
    taskFinished = pyqtSignal(object)  # 发送结果字典
    taskError = pyqtSignal(str)  # 发送错误消息
    
    # 管道初始化信号
    pipelineInitialized = pyqtSignal()
    pipelineInitError = pyqtSignal(str)
    
    # 日志信号
    logMessage = pyqtSignal(str)

    # ========== QML 调用的槽函数 ==========
    
    @pyqtSlot(str)
    def startTask(self, user_input: str):
        """由 QML 调用，启动任务执行。
        
        Args:
            user_input: 用户输入的查询文本
        """
        # 这个方法的实现在 MainWindowQML 中
        # 这里只是声明接口
        pass

    @pyqtSlot()
    def initializePipeline(self):
        """由 QML 调用，初始化管道。"""
        # 这个方法的实现在 MainWindowQML 中
        pass

    @pyqtSlot()
    def closeWindow(self):
        """由 QML 调用，关闭窗口。"""
        # 这个方法的实现在 MainWindowQML 中
        pass

    # ========== 工具方法 ==========
    
    def emit_task_finished(self, result: dict):
        """发送任务完成信号。
        
        Args:
            result: 任务结果字典
        """
        # 确保结果可以被 QML 序列化
        qml_result = self._make_qml_compatible(result)
        self.taskFinished.emit(qml_result)

    def emit_task_error(self, error: str):
        """发送任务错误信号。
        
        Args:
            error: 错误消息
        """
        self.taskError.emit(error)

    def emit_log(self, message: str):
        """发送日志消息。
        
        Args:
            message: 日志内容
        """
        self.logMessage.emit(message)

    def _make_qml_compatible(self, obj: Any) -> Any:
        """将 Python 对象转换为 QML 兼容的格式。
        
        Args:
            obj: Python 对象
            
        Returns:
            QML 兼容的对象
        """
        if isinstance(obj, dict):
            return {k: self._make_qml_compatible(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_qml_compatible(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # 其他类型转换为字符串
            return str(obj)
