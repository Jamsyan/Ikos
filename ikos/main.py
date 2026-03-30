"""Ikos 主程序入口."""

import sys

from loguru import logger

from ikos import __version__


def setup_logging(config: dict | None = None) -> None:
    """配置日志系统.

    Args:
        config: 日志配置字典
    """
    default_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.remove()
    logger.add(
        sys.stderr,
        format=default_format,
        level="INFO",
    )


def main() -> int:
    """主程序入口.

    Returns:
        int: 退出码
    """
    setup_logging()

    logger.info(f"Ikos v{__version__} - Intelligent Knowledge Building System")
    logger.info("从网络信息到结构化知识 - 多轮 AI 深度挖掘与重构平台")
    logger.warning("当前版本：架构设计完成，开发实施中")
    logger.info("访问 https://github.com/jamsyan/Ikos 了解更多")

    return 0


if __name__ == "__main__":
    sys.exit(main())
