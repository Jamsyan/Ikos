#!/usr/bin/env python
"""模型源选择演示 - 展示如何智能选择魔塔社区或 Hugging Face."""

from ikos.utils import (
    ModelSourceSelector,
    get_model_source,
    is_modelscope,
    is_huggingface
)
from ikos.utils.model_downloader import ModelDownloader


def demo_auto_detect():
    """演示自动检测。"""
    print("=" * 60)
    print("演示 1：自动检测模型源")
    print("=" * 60)
    
    selector = ModelSourceSelector(preferred="auto")
    source = selector.detect()
    
    print(f"\n检测结果：{source}")
    print(f"检测逻辑：")
    print(f"  1. 尝试连接 www.modelscope.cn:443")
    print(f"  2. 如果失败，尝试连接 huggingface.co:443")
    print(f"  3. 都失败则默认使用 modelscope")
    
    if source == "modelscope":
        print(f"\n✅ 使用魔塔社区（国内推荐）")
    else:
        print(f"\n✅ 使用 Hugging Face（国际推荐）")
    
    print()


def demo_preferred_source():
    """演示指定模型源。"""
    print("=" * 60)
    print("演示 2：指定模型源")
    print("=" * 60)
    
    # 强制使用魔塔
    selector_ms = ModelSourceSelector(preferred="modelscope")
    source_ms = selector_ms.detect()
    print(f"\n指定 'modelscope': {source_ms}")
    
    # 强制使用 Hugging Face
    selector_hf = ModelSourceSelector(preferred="huggingface")
    source_hf = selector_hf.detect()
    print(f"指定 'huggingface': {source_hf}")
    
    print()


def demo_convenience_functions():
    """演示便捷函数。"""
    print("=" * 60)
    print("演示 3：便捷函数")
    print("=" * 60)
    
    # 获取当前源
    source = get_model_source()
    print(f"\n当前模型源：{source}")
    
    # 判断是否使用魔塔
    if is_modelscope():
        print("✅ 当前使用魔塔社区")
    else:
        print("✅ 当前使用 Hugging Face")
    
    print()


def demo_download_url():
    """演示获取下载 URL。"""
    print("=" * 60)
    print("演示 4：获取下载 URL")
    print("=" * 60)
    
    selector = ModelSourceSelector(preferred="auto")
    source = selector.detect()
    
    # 示例模型 ID
    modelscope_model = "damo/nlp_csanmt_translationzh2en"
    huggingface_model = "facebook/bart-base"
    
    if source == "modelscope":
        url = selector.get_download_url(modelscope_model)
        print(f"\n魔塔社区模型：{modelscope_model}")
        print(f"下载 URL: {url}")
    else:
        url = selector.get_download_url(huggingface_model)
        print(f"\nHugging Face 模型：{huggingface_model}")
        print(f"下载 URL: {url}")
    
    print()


def demo_api_endpoint():
    """演示获取 API 端点。"""
    print("=" * 60)
    print("演示 5：获取 API 端点")
    print("=" * 60)
    
    selector = ModelSourceSelector(preferred="auto")
    endpoint = selector.get_api_endpoint()
    
    print(f"\nAPI 端点：{endpoint}")
    
    if "modelscope.cn" in endpoint:
        print("✅ 魔塔社区 API")
    else:
        print("✅ Hugging Face API")
    
    print()


def demo_downloader():
    """演示模型下载器。"""
    print("=" * 60)
    print("演示 5：模型下载器（示例）")
    print("=" * 60)
    
    print("\n示例代码:")
    print("""
from ikos.utils.model_downloader import download_model

# 自动选择最优源下载模型
model_path = download_model(
    model_id="damo/nlp_csanmt_translationzh2en",
    cache_dir="./models",
    preferred_source="auto"
)

print(f"模型已下载到：{model_path}")
    """)
    
    print("\n注意：实际下载需要网络连接和安装 modelscope/huggingface_hub")
    print()


def main():
    """主函数。"""
    print("\n" + "🚀" * 30)
    print("Ikos 智能模型源选择演示")
    print("🚀" * 30 + "\n")
    
    # 执行所有演示
    demo_auto_detect()
    demo_preferred_source()
    demo_convenience_functions()
    demo_download_url()
    demo_api_endpoint()
    demo_downloader()
    
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n更多信息请查看：docs/模型源使用指南.md")
    print()


if __name__ == "__main__":
    main()
