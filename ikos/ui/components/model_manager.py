"""模型管理面板 - 模型下载、切换与管理."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QGroupBox,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QThread
from loguru import logger


class ModelDownloadThread(QThread):
    """模型下载线程."""

    progress = pyqtSignal(int, str)  # 进度百分比，状态文本
    finished = pyqtSignal(str)  # 模型路径
    error = pyqtSignal(str)  # 错误信息

    def __init__(self, model_name: str, quantization: str = "NF4"):
        super().__init__()
        self.model_name = model_name
        self.quantization = quantization

    def run(self):
        try:
            from ikos.core import NativeModelLoader

            loader = NativeModelLoader()
            self.progress.emit(0, "开始下载...")

            # 下载模型
            model_path = loader.download_model(
                model_name=self.model_name,
                quantization=self.quantization,
            )

            self.progress.emit(100, "下载完成")
            self.finished.emit(str(model_path))

        except Exception as e:
            logger.error(f"模型下载失败：{e}")
            self.error.emit(str(e))


class ModelManagerPanel(QGroupBox):
    """模型管理面板."""

    model_selected = pyqtSignal(str)  # 模型被选中
    model_downloaded = pyqtSignal(str)  # 模型下载完成

    def __init__(self):
        super().__init__("模型管理")
        self._init_ui()
        self._refresh_cached_models()

    def _init_ui(self) -> None:
        """初始化 UI."""
        self.setStyleSheet("""
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

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # 模型选择
        select_layout = QHBoxLayout()
        select_layout.setSpacing(8)

        select_label = QLabel("选择模型:")
        select_label.setStyleSheet("color: #666666; font-size: 12px;")
        select_layout.addWidget(select_label)

        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(32)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 10px;
                color: #333333;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
        """)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        select_layout.addWidget(self.model_combo)

        layout.addLayout(select_layout)

        # 下载按钮
        self.download_btn = QPushButton("下载选中模型")
        self.download_btn.setFixedHeight(36)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
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
        self.download_btn.clicked.connect(self._download_model)
        layout.addWidget(self.download_btn)

        # 下载进度
        self.download_progress = QProgressBar()
        self.download_progress.setFixedHeight(20)
        self.download_progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: 1px solid #d9d9d9;
                border-radius: 3px;
                text-align: center;
                color: #666666;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 3px;
            }
        """)
        self.download_progress.setVisible(False)
        layout.addWidget(self.download_progress)

        # 已下载模型列表
        list_label = QLabel("已下载模型:")
        list_label.setStyleSheet("color: #666666; font-size: 12px; font-weight: bold;")
        layout.addWidget(list_label)

        self.model_list = QListWidget()
        self.model_list.setFixedHeight(150)
        self.model_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                background-color: #fafafa;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #e8e8e8;
            }
            QListWidget::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        self.model_list.itemClicked.connect(self._on_list_item_clicked)
        layout.addWidget(self.model_list)

        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet("""
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
        refresh_btn.clicked.connect(self._refresh_cached_models)
        layout.addWidget(refresh_btn)

    def _refresh_cached_models(self) -> None:
        """刷新已缓存模型列表."""
        try:
            from ikos.core import NativeModelLoader

            loader = NativeModelLoader()
            cached = loader.get_cached_models()

            self.model_list.clear()
            for model in cached:
                item = QListWidgetItem(model.get("name", "Unknown"))
                item.setData(1, model)  # 存储完整信息
                self.model_list.addItem(item)

            logger.info(f"已刷新 {len(cached)} 个缓存模型")

        except Exception as e:
            logger.error(f"刷新缓存模型失败：{e}")

    def _on_model_changed(self, model_name: str) -> None:
        """模型选择变化."""
        logger.info(f"模型选择变化：{model_name}")
        self.model_selected.emit(model_name)

    def _download_model(self) -> None:
        """下载模型."""
        model_name = self.model_combo.currentText()
        if not model_name:
            QMessageBox.warning(self, "警告", "请先选择要下载的模型")
            return

        # 禁用按钮
        self.download_btn.setEnabled(False)
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)

        # 创建下载线程
        self.download_thread = ModelDownloadThread(model_name)
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_progress(self, percent: int, status: str) -> None:
        """下载进度更新."""
        self.download_progress.setValue(percent)
        self.download_progress.setFormat(f"{percent}% - {status}")

    def _on_download_finished(self, model_path: str) -> None:
        """下载完成."""
        self.download_btn.setEnabled(True)
        self.download_progress.setVisible(False)

        QMessageBox.information(
            self,
            "下载完成",
            f"模型已下载到:\n{model_path}"
        )

        self.model_downloaded.emit(model_path)
        self._refresh_cached_models()

    def _on_download_error(self, error_msg: str) -> None:
        """下载错误."""
        self.download_btn.setEnabled(True)
        self.download_progress.setVisible(False)

        QMessageBox.critical(self, "下载失败", f"模型下载失败:\n{error_msg}")

    def _on_list_item_clicked(self, item: QListWidgetItem) -> None:
        """列表项点击."""
        model_info = item.data(1)
        if model_info:
            model_name = model_info.get("name", "")
            self.model_combo.setCurrentText(model_name)
            self.model_selected.emit(model_name)

    def add_predefined_models(self, models: list[str]) -> None:
        """添加预定义模型列表.

        Args:
            models: 模型名称列表
        """
        self.model_combo.addItems(models)

    def stop_download(self) -> None:
        """停止下载."""
        if hasattr(self, "download_thread") and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
