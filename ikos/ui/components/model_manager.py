"""模型管理面板 - 紧凑版，模型下载、切换与管理."""

from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel,
                             QMessageBox, QProgressBar, QPushButton,
                             QVBoxLayout, QWidget)


class ModelDownloadThread(QThread):
    """模型下载线程."""

    progress = pyqtSignal(int, str)  # 进度百分比，状态文本
    status = pyqtSignal(str)  # 当前状态说明
    log = pyqtSignal(str, str)  # 日志文本，日志级别
    finished = pyqtSignal(str)  # 模型路径
    error = pyqtSignal(str)  # 错误信息

    def __init__(
        self,
        model_name: str,
        quantization: str = "NF4",
        preferred_source: str = "auto",
    ):
        super().__init__()
        self.model_name = model_name
        self.quantization = quantization
        self.preferred_source = preferred_source

    @staticmethod
    def _normalize_log_type(level_name: str) -> str:
        """将 loguru 级别映射为 UI 级别。"""
        level_name = level_name.upper()
        if level_name in {"DEBUG", "INFO"}:
            return "info"
        if level_name == "SUCCESS":
            return "success"
        if level_name == "WARNING":
            return "warning"
        return "error"

    @staticmethod
    def _download_log_filter(record: dict) -> bool:
        """只转发下载链路相关日志。"""
        allowed_names = {
            "ikos.utils.model_downloader",
            "ikos.core.native_model_loader",
            "ikos.utils.cache_manager",
            "ikos.utils.model_source",
        }
        return record["name"] in allowed_names

    @staticmethod
    def _rewrite_download_message(message: str) -> str | None:
        """把底层下载日志改写成更适合 UI 展示的文本。"""
        ignored_prefixes = (
            "模型下载器已初始化",
            "缓存管理器已初始化",
            "原生模型加载器已初始化",
            "失败后自动回退",
        )
        if message.startswith(ignored_prefixes):
            return None

        replacements = {
            "开始自动检测模型源...": "正在检测可用下载源",
            "使用模型源：auto": "下载源模式：自动选择",
            "首选模型源：auto": "下载源模式：自动选择",
            "首选模型源：modelscope": "下载源模式：魔塔社区",
            "首选模型源：huggingface": "下载源模式：Hugging Face",
            "验证模型完整性...": "正在校验模型文件完整性",
            "模型完整性验证通过": "模型文件校验通过",
            "清理无用文件（README/LICENSE 等）...": "正在清理无用附带文件",
        }
        if message in replacements:
            return replacements[message]

        if message.startswith("使用模型源："):
            source = message.split("：", 1)[1]
            source_labels = {
                "auto": "自动选择",
                "modelscope": "魔塔社区",
                "huggingface": "Hugging Face",
            }
            return f"本次下载将使用：{source_labels.get(source, source)}"

        if message.startswith("开始下载模型："):
            model_name = message.split("：", 1)[1]
            return f"准备下载模型：{model_name}"

        if message.startswith("使用环境变量指定的模型源："):
            source = message.split("：", 1)[1]
            return f"已按环境变量指定下载源：{source}"

        if message.startswith("使用指定的模型源："):
            source = message.split("：", 1)[1]
            return f"已手动指定下载源：{source}"

        if message.startswith("使用魔塔社区下载："):
            return "已连接魔塔社区，开始拉取模型文件"

        if message.startswith("使用 Hugging Face 下载："):
            return "已连接 Hugging Face，开始拉取模型文件"

        if message.startswith("模型已缓存："):
            return "检测到本地缓存，跳过重复下载"

        if message.startswith("模型下载完成："):
            return "模型文件下载完成"

        if message.startswith("清理了 "):
            return message

        if message.startswith("  文件数：") or message.startswith("  总大小：") or message.startswith("  核心文件："):
            return message.strip()

        if message.startswith("从魔塔社区下载失败："):
            return "魔塔社区下载失败，正在整理错误详情"

        if message.startswith("从 Hugging Face 下载失败："):
            return "Hugging Face 下载失败，正在整理错误详情"

        return message

    def run(self):
        sink_id = logger.add(
            self._forward_log,
            level="INFO",
            format="{message}",
            filter=self._download_log_filter,
        )
        try:
            from ikos.core import NativeModelLoader

            loader = NativeModelLoader(preferred_source=self.preferred_source)
            self.progress.emit(0, "准备下载")
            self.status.emit("正在准备下载任务")

            # 下载模型
            model_path = loader.download_model(
                model_name=self.model_name,
                quantization=self.quantization,
            )

            self.progress.emit(100, "下载完成")
            self.status.emit("下载完成")
            self.finished.emit(str(model_path))

        except Exception as e:
            logger.error(f"模型下载失败：{e}")
            self.status.emit("下载失败")
            self.error.emit(str(e))
        finally:
            logger.remove(sink_id)

    def _forward_log(self, message) -> None:
        """转发下载链路日志到 UI。"""
        record = message.record
        text = record["message"].strip()
        if not text:
            return

        display_text = self._rewrite_download_message(text)
        if not display_text:
            return

        log_type = self._normalize_log_type(record["level"].name)
        self.log.emit(display_text, log_type)
        if log_type in {"info", "warning", "error"}:
            self.status.emit(display_text)


class ModelManagerPanel(QGroupBox):
    """模型管理面板 - 紧凑版."""

    model_selected = pyqtSignal(str)  # 模型被选中
    model_downloaded = pyqtSignal(str)  # 模型下载完成
    download_log = pyqtSignal(str, str)  # 下载日志
    download_status_changed = pyqtSignal(str)  # 下载状态
    download_source_changed = pyqtSignal(str)  # 下载源变化

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

        source_layout = QHBoxLayout()
        source_layout.setSpacing(6)

        source_label = QLabel("下载源")
        source_label.setStyleSheet("color: #666666; font-size: 11px;")
        source_layout.addWidget(source_label)

        self.source_combo = QComboBox()
        self.source_combo.setFixedHeight(28)
        self.source_combo.addItem("自动", "auto")
        self.source_combo.addItem("魔塔社区", "modelscope")
        self.source_combo.addItem("Hugging Face", "huggingface")
        self.source_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 8px;
                padding: 0 12px;
                color: #333333;
                font-size: 11px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                width: 24px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8c8c8c;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                border-radius: 8px;
                padding: 4px;
                background-color: white;
                color: #333333;
                selection-background-color: #e6f4ff;
                selection-color: #1890ff;
            }
        """)
        self.source_combo.currentIndexChanged.connect(self._emit_download_source_changed)
        source_layout.addWidget(self.source_combo, 1)
        layout.addLayout(source_layout)

        # 模型选择 + 下载按钮（一行）
        select_layout = QHBoxLayout()
        select_layout.setSpacing(6)

        self.model_combo = QComboBox()
        self.model_combo.setFixedHeight(30)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 8px;
                padding: 0 12px;
                color: #333333;
                font-size: 11px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                width: 24px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8c8c8c;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                border-radius: 8px;
                padding: 4px;
                background-color: white;
                color: #333333;
                selection-background-color: #e6f4ff;
                selection-color: #1890ff;
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

        self.download_status_label = QLabel("等待下载任务")
        self.download_status_label.setStyleSheet("color: #999999; font-size: 10px;")
        self.download_status_label.setWordWrap(True)
        layout.addWidget(self.download_status_label)

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

    def _emit_download_source_changed(self) -> None:
        """转发下载源变化。"""
        self.download_source_changed.emit(self.get_download_source())

    def get_download_source(self) -> str:
        """获取当前下载源配置。"""
        source = self.source_combo.currentData()
        return source if isinstance(source, str) else "auto"

    def set_download_source(self, source: str) -> None:
        """设置当前下载源配置。"""
        index = self.source_combo.findData(source)
        if index >= 0 and index != self.source_combo.currentIndex():
            self.source_combo.blockSignals(True)
            self.source_combo.setCurrentIndex(index)
            self.source_combo.blockSignals(False)

    def has_cached_model(self, model_name: str) -> bool:
        """判断指定模型是否已缓存。"""
        return model_name in self._downloaded_models

    def _set_download_status(self, status: str) -> None:
        """更新下载状态提示。"""
        self.download_status_label.setText(status)
        self.download_status_changed.emit(status)

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
        self._set_download_status("已提交下载任务，正在准备")
        self.download_log.emit(f"已提交下载任务：{model_name}", "info")

        # 创建下载线程
        self.download_thread = ModelDownloadThread(
            model_name,
            preferred_source=self.get_download_source(),
        )
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.status.connect(self._set_download_status)
        self.download_thread.log.connect(self.download_log.emit)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_download_progress(self, percent: int, status: str) -> None:
        """下载进度更新."""
        self.download_progress.setValue(percent)
        self.download_progress.setFormat(status if status else f"{percent}%")
        if status:
            self._set_download_status(status)

    def _on_download_finished(self, model_path: str) -> None:
        """下载完成."""
        self.download_btn.setEnabled(True)
        self.download_btn.setText("下载")
        self.download_progress.setVisible(False)
        self._set_download_status("下载完成，可直接使用")
        self.download_log.emit("模型下载完成，可直接使用", "success")

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
        self._set_download_status("下载失败，请查看日志详情")
        self.download_log.emit("模型下载失败，请查看详细错误信息", "error")

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
