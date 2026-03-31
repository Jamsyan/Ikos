"""UI 配置管理器 - 持久化 UI 状态与偏好."""

import json
from pathlib import Path
from typing import Any

from loguru import logger


class UIConfigManager:
    """UI 配置管理器."""

    def __init__(self, config_file: str | Path | None = None):
        """初始化配置管理器.

        Args:
            config_file: 配置文件路径
        """
        if config_file is None:
            config_file = Path("./data/ui_config.json")
        else:
            config_file = Path(config_file)

        self.config_file = config_file
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info(f"UI 配置已加载：{self.config_file}")
            except Exception as e:
                logger.error(f"加载 UI 配置失败：{e}")
                self._config = {}
        else:
            logger.info("UI 配置文件不存在，使用默认配置")
            self._config = {}

    def _save_config(self) -> None:
        """保存配置."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logger.info(f"UI 配置已保存：{self.config_file}")
        except Exception as e:
            logger.error(f"保存 UI 配置失败：{e}")

    def get_window_geometry(self) -> dict[str, int]:
        """获取窗口几何信息.

        Returns:
            dict: 窗口位置和大小
        """
        default = {
            "x": 100,
            "y": 100,
            "width": 1200,
            "height": 900,
        }
        return self._config.get("window_geometry", default)

    def set_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """设置窗口几何信息.

        Args:
            x: X 坐标
            y: Y 坐标
            width: 宽度
            height: 高度
        """
        self._config["window_geometry"] = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }
        self._save_config()

    def get_model_selection(self) -> str:
        """获取选中的模型.

        Returns:
            str: 模型名称
        """
        return self._config.get("model_selection", "Qwen 3.5 7B")

    def set_model_selection(self, model: str) -> None:
        """设置选中的模型.

        Args:
            model: 模型名称
        """
        self._config["model_selection"] = model
        self._save_config()

    def get_engine_mode(self) -> str:
        """获取引擎模式.

        Returns:
            str: 引擎模式
        """
        return self._config.get("engine_mode", "自动")

    def set_engine_mode(self, mode: str) -> None:
        """设置引擎模式.

        Args:
            mode: 引擎模式
        """
        self._config["engine_mode"] = mode
        self._save_config()

    def get_quantization_level(self) -> str:
        """获取量化等级.

        Returns:
            str: 量化等级
        """
        return self._config.get("quantization_level", "INT4")

    def set_quantization_level(self, level: str) -> None:
        """设置量化等级.

        Args:
            level: 量化等级
        """
        self._config["quantization_level"] = level
        self._save_config()

    def get_output_config(self) -> dict[str, Any]:
        """获取输出配置.

        Returns:
            dict: 输出配置
        """
        default = {
            "formats": ["markdown", "json"],
            "output_dir": "./data/output",
            "include_knowledge_graph": True,
        }
        return self._config.get("output_config", default)

    def set_output_config(self, config: dict[str, Any]) -> None:
        """设置输出配置.

        Args:
            config: 输出配置
        """
        self._config["output_config"] = config
        self._save_config()

    def get_recent_queries(self) -> list[str]:
        """获取最近的查询.

        Returns:
            list[str]: 查询列表
        """
        return self._config.get("recent_queries", [])

    def add_recent_query(self, query: str) -> None:
        """添加最近的查询.

        Args:
            query: 查询内容
        """
        queries = self.get_recent_queries()
        if query not in queries:
            queries.insert(0, query)
            queries = queries[:10]  # 只保留最近 10 条
            self._config["recent_queries"] = queries
            self._save_config()

    def clear_recent_queries(self) -> None:
        """清除最近的查询."""
        self._config["recent_queries"] = []
        self._save_config()

    def get_all_config(self) -> dict[str, Any]:
        """获取所有配置.

        Returns:
            dict: 完整配置
        """
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """重置为默认配置."""
        self._config = {}
        self._save_config()
        logger.info("UI 配置已重置为默认")
