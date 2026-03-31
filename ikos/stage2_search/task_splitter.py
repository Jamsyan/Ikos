"""任务拆分器 - 第二阶段核心组件."""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml


class TaskSplitter:
    """任务拆分器。
    
    将工程化提示词拆分为多个可并行执行的子任务。
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化任务拆分器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage2_search.yaml"
        
        self.prompts = load_yaml(config_path)
    
    def split(
        self,
        engineered_prompt: str,
        core_topic: str
    ) -> dict[str, Any]:
        """执行任务拆分。
        
        Args:
            engineered_prompt: 工程化提示词
            core_topic: 核心主题
            
        Returns:
            dict: 拆分结果
        """
        logger.info(f"开始拆分任务，核心主题：{core_topic}")
        
        prompt = self.prompts["task_splitter"].format(
            engineered_prompt=engineered_prompt,
            core_topic=core_topic
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            logger.info(f"任务拆分完成，共 {len(result.get('tasks', []))} 个子任务")
            return result
            
        except Exception as e:
            logger.error(f"任务拆分失败：{e}")
            return self._fallback_split(core_topic)
    
    def review(
        self,
        task_list: dict[str, Any],
        core_topic: str
    ) -> dict[str, Any]:
        """审核拆分后的任务列表。
        
        Args:
            task_list: 任务列表
            core_topic: 核心主题
            
        Returns:
            dict: 审核结果
        """
        logger.info("审核任务列表")
        
        prompt = self.prompts["task_reviewer"].format(
            task_list=json.dumps(task_list, ensure_ascii=False),
            core_topic=core_topic
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            
            logger.info(f"任务审核完成，通过 {len(result.get('approved_tasks', []))} 个")
            return result
            
        except Exception as e:
            logger.error(f"任务审核失败：{e}")
            return self._fallback_review(task_list)
    
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
    
    def _fallback_split(self, core_topic: str) -> dict[str, Any]:
        """备用拆分逻辑。
        
        Args:
            core_topic: 核心主题
            
        Returns:
            dict: 简化的拆分结果
        """
        return {
            "tasks": [
                {
                    "id": "task_1",
                    "name": f"{core_topic}基本概念",
                    "description": f"检索{core_topic}的基本概念和定义",
                    "search_queries": [f"{core_topic} 定义", f"{core_topic} 是什么"],
                    "expected_output": "基本概念列表"
                },
                {
                    "id": "task_2",
                    "name": f"{core_topic}核心原理",
                    "description": f"检索{core_topic}的核心原理和机制",
                    "search_queries": [f"{core_topic} 原理", f"{core_topic} 工作机制"],
                    "expected_output": "原理说明"
                },
                {
                    "id": "task_3",
                    "name": f"{core_topic}应用场景",
                    "description": f"检索{core_topic}的应用场景和案例",
                    "search_queries": [f"{core_topic} 应用", f"{core_topic} 案例"],
                    "expected_output": "应用案例列表"
                }
            ]
        }
    
    def _fallback_review(self, task_list: dict[str, Any]) -> dict[str, Any]:
        """备用审核逻辑。
        
        Args:
            task_list: 任务列表
            
        Returns:
            dict: 简化的审核结果
        """
        tasks = task_list.get("tasks", [])
        return {
            "approved_tasks": [t["id"] for t in tasks],
            "rejected_tasks": [],
            "suggestions": "无",
            "reason": "备用审核：所有任务均已通过"
        }
