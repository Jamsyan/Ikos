"""备忘录管理器 - 第二阶段核心组件."""

import json
from typing import Any
from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml
from pathlib import Path


class MemoManager:
    """备忘录管理器。
    
    管理搜索过程中发现的连锁性信息，组织评审流程。
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化备忘录管理器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        self.memo_batch: list[dict[str, Any]] = []
        self.reviewed_items: list[dict[str, Any]] = []
        self.iteration_count = 0
        self.max_iterations = 5
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage2_search.yaml"
        
        self.prompts = load_yaml(config_path)
    
    def add_items(self, items: list[dict[str, Any]]) -> None:
        """添加备忘录条目。
        
        Args:
            items: 备忘录条目列表
        """
        self.memo_batch.extend(items)
        logger.info(f"添加 {len(items)} 个备忘录条目，总计 {len(self.memo_batch)} 个")
    
    def review_batch(
        self,
        core_topic: str,
        overall_task: str
    ) -> dict[str, Any]:
        """评审当前批次的备忘录。
        
        Args:
            core_topic: 核心主题
            overall_task: 整体任务
            
        Returns:
            dict: 评审结果
        """
        if not self.memo_batch:
            logger.info("备忘录为空，无需评审")
            return self._empty_review_result()
        
        self.iteration_count += 1
        
        if self.iteration_count > self.max_iterations:
            logger.warning(f"已达到最大评审轮次：{self.max_iterations}")
            return self._terminate_review()
        
        logger.info(f"第 {self.iteration_count} 轮备忘录评审")
        
        prompt = self.prompts["memo_reviewer"].format(
            memo_batch=json.dumps(self.memo_batch, ensure_ascii=False),
            core_topic=core_topic,
            overall_task=overall_task
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            # 记录已评审的条目
            self.reviewed_items.extend(result.get("reviews", []))
            
            # 过滤掉不相关的条目
            relevant_items = [
                item for item in result.get("reviews", [])
                if item.get("is_relevant", False)
            ]
            
            logger.info(f"评审完成，{len(relevant_items)}/{len(self.memo_batch)} 条目通过")
            
            return result
            
        except Exception as e:
            logger.error(f"备忘录评审失败：{e}")
            return self._fallback_review()
    
    def make_final_decision(
        self,
        all_reviews: list[dict[str, Any]],
        current_batch: dict[str, Any]
    ) -> dict[str, Any]:
        """做出最终决策。
        
        Args:
            all_reviews: 所有评审结果
            current_batch: 当前批次数据
            
        Returns:
            dict: 最终决策
        """
        logger.info("生成最终决策")
        
        prompt = self.prompts["final_decision"].format(
            all_reviews=json.dumps(all_reviews, ensure_ascii=False),
            current_batch=json.dumps(current_batch, ensure_ascii=False)
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            decision = result.get("decision", "terminate_and_next_stage")
            logger.info(f"最终决策：{decision}")
            
            return result
            
        except Exception as e:
            logger.error(f"最终决策失败：{e}")
            return self._fallback_decision()
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """解析 JSON 响应。
        
        Args:
            content: 模型响应内容
            
        Returns:
            dict: 解析后的数据
        """
        import re
        
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("JSON 解析失败")
            return {}
    
    def _empty_review_result(self) -> dict[str, Any]:
        """空评审结果。
        
        Returns:
            dict: 空结果
        """
        return {
            "reviews": [],
            "has_valuable_items": False,
            "suggested_new_queries": []
        }
    
    def _terminate_review(self) -> dict[str, Any]:
        """终止评审结果。
        
        Returns:
            dict: 终止结果
        """
        return {
            "reviews": [],
            "has_valuable_items": False,
            "suggested_new_queries": [],
            "reason": f"已达到最大评审轮次：{self.max_iterations}"
        }
    
    def _fallback_review(self) -> dict[str, Any]:
        """备用评审逻辑。
        
        Returns:
            dict: 简化的评审结果
        """
        return {
            "reviews": [
                {
                    "memo_item": item,
                    "is_relevant": True,
                    "value": "中",
                    "continue_search": False,
                    "reason": "备用评审：默认通过"
                }
                for item in self.memo_batch[:3]
            ],
            "has_valuable_items": len(self.memo_batch) > 0,
            "suggested_new_queries": []
        }
    
    def _fallback_decision(self) -> dict[str, Any]:
        """备用决策逻辑。
        
        Returns:
            dict: 简化的决策结果
        """
        return {
            "decision": "terminate_and_next_stage",
            "reason": "备用决策：进入下一阶段",
            "new_queries": [],
            "confidence": 0.5
        }
    
    def get_all_reviewed_items(self) -> list[dict[str, Any]]:
        """获取所有已评审的条目。
        
        Returns:
            list: 已评审条目列表
        """
        return self.reviewed_items
    
    def reset(self) -> None:
        """重置管理器状态。"""
        self.memo_batch = []
        self.reviewed_items = []
        self.iteration_count = 0
