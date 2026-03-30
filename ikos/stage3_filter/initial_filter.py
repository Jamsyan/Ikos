"""初筛模块 - 第三阶段核心组件."""

import re
from typing import Any
from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml
from pathlib import Path


class InitialFilter:
    """初筛过滤器。
    
    对原始 HTML 数据进行初步筛选：
    - 去除 HTML 标签
    - 去除广告和导航
    - 去除不相关内容
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化初筛过滤器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        self.filtered_count = 0
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage3_filter.yaml"
        
        self.prompts = load_yaml(config_path)
    
    def filter_html(self, html_content: str, core_topic: str) -> dict[str, Any]:
        """过滤 HTML 内容。
        
        Args:
            html_content: 原始 HTML 内容
            core_topic: 核心主题
            
        Returns:
            dict: 过滤结果
        """
        logger.info(f"执行 HTML 初筛，内容长度：{len(html_content)}")
        
        # 去除 HTML 标签
        cleaned_text = self._remove_html_tags(html_content)
        
        # 去除广告和导航内容
        cleaned_text = self._remove_ads_and_nav(cleaned_text)
        
        # 确认相关性
        is_relevant = self._check_relevance(cleaned_text, core_topic)
        
        if not is_relevant:
            logger.warning("内容与核心主题不相关")
            return {
                "cleaned_content": "",
                "removed_sections": ["全部内容"],
                "content_type": "不相关",
                "word_count": 0,
                "is_relevant": False
            }
        
        self.filtered_count += 1
        
        return {
            "cleaned_content": cleaned_text,
            "removed_sections": ["HTML 标签", "广告", "导航"],
            "content_type": "正文",
            "word_count": len(cleaned_text.split()),
            "is_relevant": True
        }
    
    def _remove_html_tags(self, html: str) -> str:
        """去除 HTML 标签。
        
        Args:
            html: HTML 内容
            
        Returns:
            str: 纯文本
        """
        # 使用正则表达式去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html)
        
        # 去除脚本和样式内容
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 清理空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _remove_ads_and_nav(self, text: str) -> str:
        """去除广告和导航内容。
        
        Args:
            text: 文本内容
            
        Returns:
            str: 清理后的文本
        """
        # 常见广告关键词
        ad_keywords = [
            "广告", "推广", "赞助", "点击购买", "立即下载",
            "advertisement", "sponsor", "buy now", "download"
        ]
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 检查是否包含广告关键词
            if not any(keyword in line.lower() for keyword in ad_keywords):
                # 检查是否是导航链接
                if not (line.strip().startswith(('http', 'www', '/')) and len(line) < 100):
                    filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _check_relevance(self, text: str, core_topic: str) -> bool:
        """检查内容相关性。
        
        Args:
            text: 文本内容
            core_topic: 核心主题
            
        Returns:
            bool: 是否相关
        """
        # 简化实现：检查核心主题关键词是否在文本中出现
        topic_keywords = core_topic.lower().split()
        
        text_lower = text.lower()
        match_count = sum(1 for keyword in topic_keywords if keyword in text_lower)
        
        # 如果超过一半的关键词匹配，认为相关
        relevance_threshold = len(topic_keywords) * 0.5
        return match_count >= relevance_threshold
    
    def filter_batch(
        self,
        contents: list[dict[str, Any]],
        core_topic: str
    ) -> list[dict[str, Any]]:
        """批量过滤内容。
        
        Args:
            contents: 内容列表
            core_topic: 核心主题
            
        Returns:
            list: 过滤后的内容列表
        """
        logger.info(f"批量过滤 {len(contents)} 个内容")
        
        filtered_results = []
        for content in contents:
            html = content.get("html", "") or content.get("content", "")
            result = self.filter_html(html, core_topic)
            
            if result["is_relevant"]:
                result["source"] = content.get("source", {})
                filtered_results.append(result)
        
        logger.info(f"过滤完成，保留 {len(filtered_results)}/{len(contents)} 个内容")
        return filtered_results
    
    def get_statistics(self) -> dict[str, Any]:
        """获取过滤统计信息。
        
        Returns:
            dict: 统计信息
        """
        return {
            "filtered_count": self.filtered_count,
            "stage": "initial_filter"
        }
    
    def reset(self) -> None:
        """重置过滤器状态。"""
        self.filtered_count = 0
