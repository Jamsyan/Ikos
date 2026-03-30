"""需求解析器 - 第一阶段核心组件."""

import json
from typing import Any
from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml
from pathlib import Path


class RequirementParser:
    """需求解析器。
    
    将用户的自然语言输入转换为结构化的需求描述。
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化需求解析器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        
        # 加载提示词模板
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage1_parse.yaml"
        
        self.prompts = load_yaml(config_path)
        self.parse_history: list[dict[str, Any]] = []
        self.current_round = 0
        self.max_rounds = 10
    
    def parse(self, user_input: str) -> dict[str, Any]:
        """执行初始需求解析。
        
        Args:
            user_input: 用户自然语言输入
            
        Returns:
            dict: 解析结果
        """
        logger.info(f"开始解析用户需求：{user_input[:50]}...")
        
        # 使用初始解析提示词
        prompt = self.prompts["initial_parse"].format(user_input=user_input)
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            # 解析 JSON 响应
            result = self._parse_json_response(response.content)
            
            # 记录解析历史
            self.parse_history.append({
                "round": self.current_round,
                "type": "initial_parse",
                "input": user_input,
                "result": result
            })
            
            logger.info(f"初始解析完成，复杂度：{result.get('complexity', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"需求解析失败：{e}")
            return self._fallback_parse(user_input)
    
    def extend(self, core_topic: str, previous_result: dict[str, Any]) -> dict[str, Any]:
        """执行扩展解析。
        
        Args:
            core_topic: 核心主题
            previous_result: 上一轮解析结果
            
        Returns:
            dict: 扩展解析结果
        """
        self.current_round += 1
        
        if self.current_round > self.max_rounds:
            logger.warning(f"已达到最大解析轮次：{self.max_rounds}")
            return {"extensions": [], "should_stop": True}
        
        logger.info(f"第 {self.current_round} 轮扩展解析")
        
        # 使用扩展提示词
        prompt = self.prompts["extend_parse"].format(
            core_topic=core_topic,
            previous_result=json.dumps(previous_result, ensure_ascii=False)
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            # 记录解析历史
            self.parse_history.append({
                "round": self.current_round,
                "type": "extend_parse",
                "core_topic": core_topic,
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"扩展解析失败：{e}")
            return {"extensions": [], "should_stop": True}
    
    def generate_final_prompt(
        self,
        core_topic: str,
        core_circle: dict[str, Any]
    ) -> dict[str, Any]:
        """生成最终的工程化提示词。
        
        Args:
            core_topic: 核心主题
            core_circle: 核心圈定义
            
        Returns:
            dict: 工程化提示词
        """
        logger.info("生成最终工程化提示词")
        
        # 准备解析历史摘要
        history_summary = self._summarize_history()
        
        prompt = self.prompts["final_prompt"].format(
            parse_history=history_summary,
            validation_results="[]",  # 0.1.0 版本暂不实现验证
            core_circle=json.dumps(core_circle, ensure_ascii=False)
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            logger.info("工程化提示词生成完成")
            return result
            
        except Exception as e:
            logger.error(f"生成最终提示词失败：{e}")
            return self._fallback_final_prompt(core_topic)
    
    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """解析模型的 JSON 响应。
        
        Args:
            content: 模型响应内容
            
        Returns:
            dict: 解析后的 JSON 数据
        """
        # 尝试提取 JSON 内容
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试直接解析
            json_str = content
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"JSON 解析失败，使用备用解析")
            return {}
    
    def _fallback_parse(self, user_input: str) -> dict[str, Any]:
        """备用解析逻辑（当模型调用失败时）。
        
        Args:
            user_input: 用户输入
            
        Returns:
            dict: 简化的解析结果
        """
        return {
            "core_need": user_input,
            "key_concepts": [user_input.split()[0] if user_input.split() else "unknown"],
            "complexity": "简单",
            "suggested_rounds": 1
        }
    
    def _fallback_final_prompt(self, core_topic: str) -> dict[str, Any]:
        """备用最终提示词生成。
        
        Args:
            core_topic: 核心主题
            
        Returns:
            dict: 简化的工程化提示词
        """
        return {
            "goal": f"检索关于{core_topic}的知识",
            "dimensions": ["基本概念", "核心原理", "应用场景"],
            "quality_criteria": ["准确性", "完整性", "权威性"],
            "final_prompt": f"请详细检索{core_topic}的相关知识，包括基本概念、核心原理和应用场景。"
        }
    
    def _summarize_history(self) -> str:
        """总结解析历史。
        
        Returns:
            str: 历史摘要
        """
        if not self.parse_history:
            return "无解析历史"
        
        summary_lines = []
        for record in self.parse_history:
            summary_lines.append(f"第{record['round']}轮：{record['type']}")
        
        return "\n".join(summary_lines)
    
    def reset(self) -> None:
        """重置解析器状态。"""
        self.parse_history = []
        self.current_round = 0
