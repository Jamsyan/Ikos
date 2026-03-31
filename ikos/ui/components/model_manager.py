"""模型管理面板 - 紧凑版，模型下载、切换与管理."""

from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QProgressBar, QPushButton,
                             QVBoxLayout, QWidget)


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
    """模型管理面板 - 紧凑版."""

    model_selected = pyqtSignal(str)  # 模型被选中
    model_downloaded = pyqtSignal(str)  # 模型下载完成

    def __init__(self):
        super().__init__("模型管理")
        self._downloaded_models = []
        self._init_ui()
        self._refresh_cached_models()

    def _init_ui(self) -> None:
        """初始化 UI - 紧凑布局."""
        self.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #333333;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #333333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 8, 10, 8)

        # 模型选择 + 下载按钮（一行）
        select_layout = QHBoxLayout()
        select_layout.setSpacing(6)

        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(30)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 0 8px;
                color: #333333;
                font-size: 11px;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
        """)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        select_layout.addWidget(self.model_combo)

        self.download_btn = QPushButton("下载")
        self.download_btn.setFixedHeight(30)
        self.download_btn.setFixedWidth(72)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
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
        select_layout.addWidget(self.download_btn)

        layout.addLayout(select_layout)

        # 下载进度（小型）
        self.download_progress = QProgressBar()
        self.download_progress.setFixedHeight(16)
        self.download_progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: 1px solid #d9d9d9;
                border-radius: 2px;
                text-align: center;
                color: #666666;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 2px;
            }
        """)
        self.download_progress.setVisible(False)
        layout.addWidget(self.download_progress)

        # 已下载模型标签
        list_label = QLabel("已下载:")
        list_label.setStyleSheet("color: #999999; font-size: 10px; font-weight: bold;")
        layout.addWidget(list_label)

        # 已下载模型（使用 Flow 布局的标签）
        self.downloaded_models_widget = QWidget()
        self.downloaded_models_layout = QHBoxLayout(self.downloaded_models_widget)
        self.downloaded_models_layout.setSpacing(4)
        self.downloaded_models_layout.setContentsMargins(0, 0, 0, 0)
        self.downloaded_models_layout.addStretch()
        layout.addWidget(self.downloaded_models_widget)

        # 刷新按钮
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setFixedHeight(28)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #666666;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_cached_models)
        layout.addWidget(refresh_btn)

    def _create_model_tag(self, model_name: str) -> QLabel:
        """创建模型标签.

        Args:
            model_name: 模型名称

        Returns:
            QLabel: 标签组件
        """
        # 简化模型名称显示
        short_name = model_name.split("/")[-1] if "/" in model_name else model_name
        if len(short_name) > 20:
            short_name = short_name[:17] + "..."

        tag = QLabel(short_name)
        tag.setStyleSheet("""
            QLabel {
                background-color: #e6f7ff;
                border: 1px solid #1890ff;
                border-radius: 3px;
                padding: 2px 6px;
                color: #1890ff;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        tag.setToolTip(model_name)
        return tag

    def _refresh_cached_models(self) -> None:
        """刷新已缓存模型列表."""
        try:
            from ikos.core import NativeModelLoader

            loader = NativeModelLoader()
            # 使用 get_cached_models 或返回空列表
            try:
                cached = loader.get_cached_models()
            except AttributeError:
                # 如果方法不存在，返回空列表
                cached = []

            # 清空现有标签
            self._downloaded_models = []
            
            # 清空布局
            while self.downloaded_models_layout.count() > 1:
                item = self.downloaded_models_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 添加新标签
            if not cached:
                empty_label = QLabel("暂无已缓存模型")
                empty_label.setStyleSheet("color: #bfbfbf; font-size: 10px;")
                self.downloaded_models_layout.insertWidget(0, empty_label)
            else:
                for model in cached:
                    if isinstance(model, dict):
                        model_name = model.get("name", "Unknown")
                    else:
                        model_name = str(model)

                    tag = self._create_model_tag(model_name)
                    self.downloaded_models_layout.insertWidget(
                        self.downloaded_models_layout.count() - 1,
                        tag
                    )
                    self._downloaded_models.append(model_name)

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
        self.download_btn.setText("处理中")
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_progress.setFormat("准备下载")

        # 创建下载线程
        self.download_thread = ModelDownloadThread(model_name)
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_progress(self, percent: int, status: str) -> None:
        """下载进度更新."""
        self.download_progress.setValue(percent)
        self.download_progress.setFormat(status if status else f"{percent}%")

    def _on_download_finished(self, model_path: str) -> None:
        """下载完成."""
        self.download_btn.setEnabled(True)
        self.download_btn.setText("下载")
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
        self.download_btn.setText("下载")
        self.download_progress.setVisible(False)

        QMessageBox.critical(self, "下载失败", f"模型下载失败：\n{error_msg}")

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
