"""旁系监督器 - 第一阶段核心组件."""

import json
from typing import Any
from loguru import logger

from ikos.core import ModelProvider


class SideSupervisor:
    """旁系监督器。
    
    监控需求解析方向是否跑偏，确保不偏离核心主题。
    """
    
    def __init__(self, model_provider: ModelProvider):
        """初始化旁系监督器。
        
        Args:
            model_provider: 模型提供者
        """
        self.model_provider = model_provider
        self.deviation_history: list[float] = []
    
    def monitor(
        self,
        parse_history: list[dict[str, Any]],
        core_topic: str
    ) -> dict[str, Any]:
        """监控解析方向。
        
        Args:
            parse_history: 解析历史
            core_topic: 核心主题
            
        Returns:
            dict: 监控结果
        """
        logger.info("执行旁系监督")
        
        # 简化实现：基于规则判断偏离程度
        deviation_score = self._calculate_deviation(parse_history, core_topic)
        
        # 记录偏离历史
        self.deviation_history.append(deviation_score)
        
        # 判断是否需要验证
        need_validation = deviation_score > 0.5
        
        # 判断是否应该终止
        should_terminate = deviation_score > 0.8 or len(self.deviation_history) >= 10
        
        result = {
            "deviation_score": deviation_score,
            "need_validation": need_validation,
            "should_terminate": should_terminate,
            "reason": self._generate_reason(deviation_score)
        }
        
        logger.info(f"监督结果：偏离指数={deviation_score:.2f}")
        return result
    
    def _calculate_deviation(
        self,
        parse_history: list[dict[str, Any]],
        core_topic: str
    ) -> float:
        """计算偏离指数。
        
        Args:
            parse_history: 解析历史
            core_topic: 核心主题
            
        Returns:
            float: 偏离指数 (0-1)
        """
        if not parse_history:
            return 0.0
        
        # 简化实现：检查关键词相似度
        # 实际应该使用更复杂的语义相似度算法
        
        # 提取核心主题的关键词
        core_keywords = set(core_topic.lower().split())
        
        # 检查最近的解析结果
        recent_records = parse_history[-3:]
        
        total_similarity = 0.0
        for record in recent_records:
            # 提取解析中的关键词
            if "result" in record and isinstance(record["result"], dict):
                concepts = record["result"].get("key_concepts", [])
                for concept in concepts:
                    concept_words = set(concept.lower().split())
                    # 计算 Jaccard 相似度
                    intersection = len(core_keywords & concept_words)
                    union = len(core_keywords | concept_words)
                    similarity = intersection / union if union > 0 else 0.0
                    total_similarity += similarity
        
        avg_similarity = total_similarity / max(1, len(recent_records) * 3)
        
        # 偏离指数 = 1 - 相似度
        deviation = 1.0 - avg_similarity
        
        return min(1.0, max(0.0, deviation))
    
    def _generate_reason(self, deviation_score: float) -> str:
        """生成监督理由。
        
        Args:
            deviation_score: 偏离指数
            
        Returns:
            str: 监督理由
        """
        if deviation_score < 0.3:
            return "解析方向与核心主题高度一致"
        elif deviation_score < 0.5:
            return "解析方向基本一致，略有偏离"
        elif deviation_score < 0.7:
            return "解析方向有明显偏离，需要注意"
        else:
            return "解析方向严重偏离，建议终止或重新验证"
    
    def get_average_deviation(self) -> float:
        """获取平均偏离指数。
        
        Returns:
            float: 平均偏离指数
        """
        if not self.deviation_history:
            return 0.0
        
        return sum(self.deviation_history) / len(self.deviation_history)
    
    def reset(self) -> None:
        """重置监督器状态。"""
        self.deviation_history = []
