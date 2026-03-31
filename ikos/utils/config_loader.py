"""配置文件加载工具."""

from pathlib import Path
from typing import Any

import yaml


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

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: str | Path = "config/settings.yaml") -> dict[str, Any]:
    """加载主配置文件。

    Args:
        config_path: 配置文件路径，默认为 config/settings.yaml

    Returns:
        dict: 配置字典
    """
    return load_yaml(config_path)


def format_prompt(template: str, **kwargs: Any) -> str:
    """安全地格式化提示词模板。

    用 str.replace 逐个替换占位符，避免 Python str.format() 将模板中的
    JSON 示例 {...} 误识别为格式字段导致 KeyError。

    Args:
        template: 提示词模板字符串
        **kwargs: 要替换的变量

    Returns:
        str: 替换后的提示词
    """
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result
