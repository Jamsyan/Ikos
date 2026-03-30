"""数据合并器 - 第三阶段核心组件."""

import json
from typing import Any
from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml
from pathlib import Path


class DataMerger:
    """数据合并器。
    
    整合所有清洗后的数据：
    - 数据去重
    - 确认相关性
    - 信息筛选
    - 构建初步知识图谱
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化数据合并器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        self.merged_data: list[dict[str, Any]] = []
        self.knowledge_graph: dict[str, Any] = {"nodes": [], "edges": []}
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage3_filter.yaml"
        
        self.prompts = load_yaml(config_path)
    
    def merge(
        self,
        filtered_data: list[dict[str, Any]],
        core_topic: str
    ) -> dict[str, Any]:
        """合并过滤后的数据。
        
        Args:
            filtered_data: 过滤后的数据列表
            core_topic: 核心主题
            
        Returns:
            dict: 合并结果
        """
        logger.info(f"开始合并 {len(filtered_data)} 个数据项")
        
        # 去重
        deduplicated = self._deduplicate(filtered_data)
        logger.info(f"去重后剩余 {len(deduplicated)} 个数据项")
        
        # 确认相关性
        relevant_data = self._confirm_relevance(deduplicated, core_topic)
        logger.info(f"相关性确认后剩余 {len(relevant_data)} 个数据项")
        
        # 信息筛选
        selected_data = self._select_information(relevant_data)
        
        # 构建知识图谱
        self.knowledge_graph = self._build_knowledge_graph(selected_data, core_topic)
        
        # 合并数据
        merged_content = self._merge_content(selected_data)
        
        self.merged_data = selected_data
        
        result = {
            "merged_data": merged_content,
            "duplicates_removed": len(filtered_data) - len(deduplicated),
            "irrelevant_removed": len(deduplicated) - len(relevant_data),
            "knowledge_graph": self.knowledge_graph,
            "final_count": len(selected_data)
        }
        
        logger.info(f"数据合并完成，最终 {len(selected_data)} 个数据项")
        return result
    
    def _deduplicate(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """去重。
        
        Args:
            data: 数据列表
            
        Returns:
            list: 去重后的数据
        """
        seen_urls = set()
        unique_data = []
        
        for item in data:
            url = item.get("url", "") or item.get("source", {}).get("url", "")
            
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_data.append(item)
            elif not url:
                # 没有 URL 的内容，检查内容相似度
                content = item.get("cleaned_content", "")
                if not any(content in existing.get("cleaned_content", "") for existing in unique_data):
                    unique_data.append(item)
        
        return unique_data
    
    def _confirm_relevance(
        self,
        data: list[dict[str, Any]],
        core_topic: str
    ) -> list[dict[str, Any]]:
        """确认相关性。
        
        Args:
            data: 数据列表
            core_topic: 核心主题
            
        Returns:
            list: 相关数据
        """
        relevant_data = []
        topic_keywords = set(core_topic.lower().split())
        
        for item in data:
            content = item.get("cleaned_content", "").lower()
            
            # 检查关键词匹配
            match_count = sum(1 for keyword in topic_keywords if keyword in content)
            
            if match_count >= len(topic_keywords) * 0.3:  # 30% 匹配度
                relevant_data.append(item)
        
        return relevant_data
    
    def _select_information(
        self,
        data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """信息筛选。
        
        Args:
            data: 数据列表
            
        Returns:
            list: 筛选后的数据
        """
        # 按质量和可信度排序
        sorted_data = sorted(
            data,
            key=lambda x: (
                x.get("reliability", 0),
                x.get("word_count", 0)
            ),
            reverse=True
        )
        
        # 保留前 20 个高质量数据
        return sorted_data[:20]
    
    def _build_knowledge_graph(
        self,
        data: list[dict[str, Any]],
        core_topic: str
    ) -> dict[str, Any]:
        """构建知识图谱。
        
        Args:
            data: 数据列表
            core_topic: 核心主题
            
        Returns:
            dict: 知识图谱
        """
        nodes = []
        edges = []
        
        # 添加核心主题节点
        nodes.append({
            "id": "core",
            "label": core_topic,
            "type": "concept",
            "description": f"核心主题：{core_topic}"
        })
        
        # 从数据中提取实体和关系（简化实现）
        node_id = 1
        for item in data[:10]:  # 限制节点数量
            title = item.get("source", {}).get("title", "")
            
            if title and title != core_topic:
                # 添加相关概念节点
                nodes.append({
                    "id": f"node_{node_id}",
                    "label": title,
                    "type": "related_concept",
                    "description": item.get("cleaned_content", "")[:200]
                })
                
                # 添加到核心主题的边
                edges.append({
                    "source": "core",
                    "target": f"node_{node_id}",
                    "relation": "related_to"
                })
                
                node_id += 1
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "core_topic": core_topic,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
    
    def _merge_content(self, data: list[dict[str, Any]]) -> str:
        """合并内容。
        
        Args:
            data: 数据列表
            
        Returns:
            str: 合并后的内容
        """
        contents = []
        
        for i, item in enumerate(data):
            content = item.get("cleaned_content", "")
            if content:
                contents.append(f"## 来源 {i+1}\n{content}")
        
        return "\n\n".join(contents)
    
    def get_knowledge_graph(self) -> dict[str, Any]:
        """获取知识图谱。
        
        Returns:
            dict: 知识图谱
        """
        return self.knowledge_graph
    
    def get_merged_data(self) -> list[dict[str, Any]]:
        """获取合并后的数据。
        
        Returns:
            list: 合并后的数据
        """
        return self.merged_data
    
    def reset(self) -> None:
        """重置合并器状态。"""
        self.merged_data = []
        self.knowledge_graph = {"nodes": [], "edges": []}
