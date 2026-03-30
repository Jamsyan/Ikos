"""Ikos 主程序入口."""

import sys
from loguru import logger

from ikos.core.pipeline import IkosPipeline
from ikos.utils.logger import setup_logger


def main():
    """Ikos 主函数。"""
    # 检查是否启动 UI
    if len(sys.argv) > 1 and sys.argv[1] in ["--ui", "-u"]:
        from ikos.ui import run_ui
        run_ui()
        return
    
    setup_logger(log_file="./data/logs/ikos.log", level="INFO")
    
    logger.info("=" * 60)
    logger.info("Ikos - Intelligent Knowledge Building System")
    logger.info("版本：0.1.0")
    logger.info("=" * 60)
    
    if len(sys.argv) < 2:
        logger.info("用法：ikos <用户输入> [选项]")
        logger.info("选项:")
        logger.info("  --ui, -u    启动图形界面")
        logger.info("示例:")
        logger.info("  ikos '我想知道傅里叶变换的数学知识'")
        logger.info("  ikos --ui")
        sys.exit(1)
    
    user_input = sys.argv[1]
    
    output_config = {"output_type": "file", "formats": ["json", "markdown"]}
    
    if len(sys.argv) > 2 and "--output-format" in sys.argv:
        idx = sys.argv.index("--output-format")
        if idx + 1 < len(sys.argv):
            formats = sys.argv[idx + 1].split(",")
            output_config["formats"] = formats
    
    logger.info(f"用户输入：{user_input}")
    logger.info(f"输出配置：{output_config}")
    
    try:
        pipeline = IkosPipeline()
        
        result = pipeline.run(user_input, output_config)
        
        if result["status"] == "success":
            logger.info("流程执行成功")
            logger.info("知识构建完成！")
            logger.info("输出文件:")
            for file_info in result.get("output_files", []):
                logger.info(f"  - {file_info.get('filename', 'unknown')} ({file_info.get('path', 'unknown')})")
        else:
            logger.error(f"流程执行失败：{result.get('error', 'unknown error')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序异常：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
