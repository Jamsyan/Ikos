"""配置文件加载工具."""

import yaml
from pathlib import Path
from typing import Any


def load_yaml(path: str | Path) -> dict[str, Any]:
    """加载 YAML 配置文件。

    Args:
        path: 配置文件路径

    Returns:
        dict: 配置字典

    Raises:
        FileNotFoundError: 文件不存在
        yaml.YAMLError: YAML 解析失败
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    """加载主配置文件。

    Args:
        config_path: 配置文件路径，默认为 config/settings.yaml

    Returns:
        dict: 配置字典
    """
    return load_yaml(config_path)
