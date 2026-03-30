"""Ikos 主程序入口."""

import sys
from pathlib import Path
from loguru import logger

from ikos.core.pipeline import IkosPipeline
from ikos.utils.logger import setup_logger


def main():
    """Ikos 主函数。"""
    # 初始化日志
    setup_logger(log_file="./data/logs/ikos.log", level="INFO")
    
    logger.info("=" * 60)
    logger.info("Ikos - Intelligent Knowledge Building System")
    logger.info("版本：0.1.0")
    logger.info("=" * 60)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法：ikos <用户输入> [输出配置]")
        print("\n示例:")
        print("  ikos '我想知道傅里叶变换的数学知识'")
        print("  ikos '量子力学基础概念' --output-format json,markdown")
        sys.exit(1)
    
    # 获取用户输入
    user_input = sys.argv[1]
    
    # 解析输出配置
    output_config = {"output_type": "file", "formats": ["json", "markdown"]}
    
    if len(sys.argv) > 2:
        if "--output-format" in sys.argv:
            idx = sys.argv.index("--output-format")
            if idx + 1 < len(sys.argv):
                formats = sys.argv[idx + 1].split(",")
                output_config["formats"] = formats
    
    logger.info(f"用户输入：{user_input}")
    logger.info(f"输出配置：{output_config}")
    
    try:
        # 创建管道
        pipeline = IkosPipeline()
        
        # 执行流程
        result = pipeline.run(user_input, output_config)
        
        # 输出结果
        if result["status"] == "success":
            logger.info("✅ 流程执行成功")
            print("\n✅ 知识构建完成！")
            print(f"\n输出文件:")
            for file_info in result.get("output_files", []):
                print(f"  - {file_info.get('filename', 'unknown')} ({file_info.get('path', 'unknown')})")
        else:
            logger.error(f"❌ 流程执行失败：{result.get('error', 'unknown error')}")
            print(f"\n❌ 流程执行失败：{result.get('error', 'unknown error')}")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        print("\n⚠️  用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序异常：{e}")
        print(f"\n❌ 程序异常：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
