"""日志配置工具."""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    log_file: str | Path | None = None,
    level: str = "INFO",
    format_str: str | None = None,
    rotation: str = "100 MB",
    retention: str = "7 days",
) -> None:
    """设置日志配置。

    Args:
        log_file: 日志文件路径，None 表示只输出到控制台
        level: 日志级别
        format_str: 日志格式字符串
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    logger.remove()

    if format_str is None:
        format_str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"

    logger.add(
        sys.stderr,
        level=level,
        format=format_str,
        colorize=True,
    )

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            level=level,
            format=format_str,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

    logger.info(f"日志系统已初始化，级别：{level}")
