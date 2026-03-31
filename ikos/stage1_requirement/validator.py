"""网络验证器 - 第一阶段核心组件."""

import json
from typing import Any

from loguru import logger

from ikos.core import ModelProvider, SearchProvider


class NetworkValidator:
    """网络验证器。
    
    对知识点进行网络搜索验证，避免模型幻觉。
    """
    
    def __init__(self, model_provider: ModelProvider, search_provider: SearchProvider):
        """初始化网络验证器。
        
        Args:
            model_provider: 模型提供者
            search_provider: 搜索提供者
        """
        self.model_provider = model_provider
        self.search_provider = search_provider
        self.validation_results: list[dict[str, Any]] = []
    
    def validate(self, knowledge_point: str, core_topic: str) -> dict[str, Any]:
        """验证知识点。
        
        Args:
            knowledge_point: 待验证的知识点
            core_topic: 核心主题
            
        Returns:
            dict: 验证结果
        """
        logger.info(f"开始验证知识点：{knowledge_point[:50]}...")
        
        # 生成搜索查询
        queries = self._generate_queries(knowledge_point, core_topic)
        
        if not queries:
            logger.warning("无法生成搜索查询")
            return self._fallback_validate(knowledge_point)
        
        # 执行搜索验证
        search_results = []
        for query in queries:
            try:
                results = self.search_provider.search(query, max_results=3)
                search_results.extend(results)
            except Exception as e:
                logger.warning(f"搜索失败 {query}: {e}")
        
        # 分析搜索结果
        validation_result = self._analyze_results(
            knowledge_point,
            search_results
        )
        
        # 记录验证结果
        self.validation_results.append({
            "knowledge_point": knowledge_point,
            "result": validation_result
        })
        
        return validation_result
    
    def _generate_queries(
        self,
        knowledge_point: str,
        core_topic: str
    ) -> list[str]:
        """生成验证查询。
        
        Args:
            knowledge_point: 知识点
            core_topic: 核心主题
            
        Returns:
            list[str]: 查询列表
        """
        # 0.1.0 版本简化实现，直接生成查询
        queries = [
            f"{core_topic} {knowledge_point}",
            f"{knowledge_point} 原理",
            f"{knowledge_point} 定义"
        ]
        
        return queries
    
    def _analyze_results(
        self,
        knowledge_point: str,
        search_results: list[Any]
    ) -> dict[str, Any]:
        """分析搜索结果。
        
        Args:
            knowledge_point: 知识点
            search_results: 搜索结果
            
        Returns:
            dict: 验证结果
        """
        if not search_results:
            return {
                "verified": False,
                "confidence": 0.0,
                "evidence": [],
                "reason": "未找到相关搜索结果"
            }
        
        # 简化实现：根据搜索结果数量判断
        confidence = min(1.0, len(search_results) / 5.0)
        
        evidence = [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet
            }
            for r in search_results[:3]
        ]
        
        return {
            "verified": confidence > 0.5,
            "confidence": confidence,
            "evidence": evidence,
            "reason": f"找到 {len(search_results)} 个相关结果"
        }
    
    def _fallback_validate(self, knowledge_point: str) -> dict[str, Any]:
        """备用验证逻辑。
        
        Args:
            knowledge_point: 知识点
            
        Returns:
            dict: 验证结果
        """
        return {
            "verified": False,
            "confidence": 0.0,
            "evidence": [],
            "reason": "验证过程失败"
        }
    
    def get_all_results(self) -> list[dict[str, Any]]:
        """获取所有验证结果。
        
        Returns:
            list: 验证结果列表
        """
        return self.validation_results
    
    def reset(self) -> None:
        """重置验证器状态。"""
        self.validation_results = []
