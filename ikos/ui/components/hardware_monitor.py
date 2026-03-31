"""硬件监控面板 - 紧凑版，实时显示 GPU/CPU/内存状态."""

from loguru import logger
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QProgressBar,
                             QVBoxLayout, QWidget)


class HardwareMonitorPanel(QGroupBox):
    """硬件监控面板 - 紧凑版."""

    def __init__(self, update_interval: int = 2000):
        """初始化硬件监控面板.

        Args:
            update_interval: 更新间隔（毫秒）
        """
        super().__init__("硬件监控")
        self.update_interval = update_interval
        self._hardware_info = None
        self._vram_manager = None

        self._init_ui()
        self._start_monitoring()

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

        # 第一行：GPU + 显存
        gpu_layout = QHBoxLayout()
        gpu_layout.setSpacing(8)

        self.gpu_label = QLabel("GPU: 检测中...")
        self.gpu_label.setStyleSheet("color: #666666; font-size: 11px;")
        self.gpu_label.setWordWrap(True)
        gpu_layout.addWidget(self.gpu_label)

        # 显存进度条（小型）
        self.vram_progress = QProgressBar()
        self.vram_progress.setFixedHeight(16)
        self.vram_progress.setFixedWidth(100)
        self.vram_progress.setStyleSheet("""
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
        gpu_layout.addWidget(self.vram_progress)

        self.vram_value_label = QLabel("0/0GB")
        self.vram_value_label.setStyleSheet("color: #333333; font-size: 10px; min-width: 50px;")
        gpu_layout.addWidget(self.vram_value_label)

        layout.addLayout(gpu_layout)

        # 第二行：CPU + 内存
        cpu_layout = QHBoxLayout()
        cpu_layout.setSpacing(8)

        self.cpu_label = QLabel("CPU: 检测中...")
        self.cpu_label.setStyleSheet("color: #666666; font-size: 11px;")
        cpu_layout.addWidget(self.cpu_label)

        # 内存进度条（小型）
        self.ram_progress = QProgressBar()
        self.ram_progress.setFixedHeight(16)
        self.ram_progress.setFixedWidth(100)
        self.ram_progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: 1px solid #d9d9d9;
                border-radius: 2px;
                text-align: center;
                color: #666666;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background-color: #52c41a;
                border-radius: 2px;
            }
        """)
        cpu_layout.addWidget(self.ram_progress)

        self.ram_value_label = QLabel("0/0GB")
        self.ram_value_label.setStyleSheet("color: #333333; font-size: 10px; min-width: 50px;")
        cpu_layout.addWidget(self.ram_value_label)

        layout.addLayout(cpu_layout)

        # 第三行：引擎模式
        engine_layout = QHBoxLayout()
        engine_layout.setSpacing(6)

        engine_label = QLabel("引擎:")
        engine_label.setStyleSheet("color: #999999; font-size: 10px;")
        engine_layout.addWidget(engine_label)

        self.engine_mode_label = QLabel("未选择")
        self.engine_mode_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #d9d9d9;
                border-radius: 3px;
                padding: 2px 8px;
                color: #666666;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        engine_layout.addWidget(self.engine_mode_label)
        engine_layout.addStretch()

        layout.addLayout(engine_layout)

    def _start_monitoring(self) -> None:
        """启动监控."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_hardware_info)
        self.timer.start(self.update_interval)
        logger.debug("硬件监控已启动")

    def _update_hardware_info(self) -> None:
        """更新硬件信息."""
        try:
            from ikos.core import detect_hardware

            # 定时刷新只更新 UI，避免把同一批硬件状态反复写进日志。
            logger.disable("ikos.core.hardware_detector")
            try:
                self._hardware_info = detect_hardware()
            finally:
                logger.enable("ikos.core.hardware_detector")

            # 更新 GPU 信息
            if self._hardware_info.gpu_model:
                self.gpu_label.setText(
                    f"GPU: {self._hardware_info.gpu_model} "
                    f"({self._hardware_info.gpu_memory_gb:.1f}GB)"
                )
            else:
                self.gpu_label.setText("GPU: 未检测到独立 GPU")

            # 更新显存使用
            if self._vram_manager:
                usage = self._vram_manager.get_usage()
                total = usage.get("total_gb", self._hardware_info.gpu_memory_gb)
                used = total - usage.get("available_gb", 0)

                if total > 0:
                    percent = int((used / total) * 100)
                    self.vram_progress.setValue(percent)
                    self.vram_progress.setFormat(f"{percent}%")
                    self.vram_value_label.setText(f"{used:.1f}/{total:.1f}GB")

            # 更新 CPU 信息
            self.cpu_label.setText(
                f"CPU: {self._hardware_info.cpu_physical_cores}C/{self._hardware_info.cpu_cores}T"
            )

            # 更新内存使用
            total_ram = self._hardware_info.system_memory_gb
            available_ram = self._hardware_info.available_memory_gb
            used_ram = total_ram - available_ram

            if total_ram > 0:
                ram_percent = int((used_ram / total_ram) * 100)
                self.ram_progress.setValue(ram_percent)
                self.ram_progress.setFormat(f"{ram_percent}%")
                self.ram_value_label.setText(f"{used_ram:.1f}/{total_ram:.1f}GB")

        except Exception as e:
            logger.error(f"更新硬件信息失败：{e}")

    def set_vram_manager(self, vram_manager) -> None:
        """设置显存管理器.

        Args:
            vram_manager: VRAMManager 实例
        """
        self._vram_manager = vram_manager

    def set_engine_mode(self, mode: str) -> None:
        """设置引擎模式.

        Args:
            mode: 引擎模式
        """
        self.engine_mode_label.setText(mode)

        # 根据模式更新颜色
        color_map = {
            "原生引擎": ("#e6f7ff", "#1890ff"),
            "混合模式": ("#fff7e6", "#fa8c16"),
            "外部引擎": ("#f6ffed", "#52c41a"),
            "自动": ("#f0f0f0", "#666666"),
        }

        bg_color, text_color = color_map.get(mode, ("#f0f0f0", "#666666"))
        self.engine_mode_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border: 1px solid {text_color};
                border-radius: 3px;
                padding: 2px 8px;
                color: {text_color};
                font-weight: bold;
                font-size: 10px;
            }}
        """)

    def stop_monitoring(self) -> None:
        """停止监控."""
        if hasattr(self, "timer"):
            self.timer.stop()
            logger.debug("硬件监控已停止")
