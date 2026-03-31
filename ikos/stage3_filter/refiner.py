"""数据精筛与重写模块 - 第三阶段核心组件."""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import format_prompt, load_yaml


class DataRefiner:
    """数据精筛与重写器。

    对合并后的数据进行精筛和模型重写。
    """

    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化精筛与重写器。

        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        self.refined_data: dict[str, Any] = {}

        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "prompts" / "stage3_filter.yaml"
            )

        self.prompts = load_yaml(config_path)

    def refine(
        self, merged_data: str, knowledge_graph: dict[str, Any], core_topic: str
    ) -> dict[str, Any]:
        """精筛数据。

        Args:
            merged_data: 合并后的数据
            knowledge_graph: 知识图谱
            core_topic: 核心主题

        Returns:
            dict: 精筛结果
        """
        logger.info("执行数据精筛")

        prompt = format_prompt(
            self.prompts["refinement_filter"],
            split_data=merged_data[:2000],
            core_topic=core_topic,
            knowledge_graph=json.dumps(knowledge_graph, ensure_ascii=False),
        )

        try:
            response = self.model_provider.call(prompt=prompt, model="qwen3.5:7b")

            result = self._parse_json_response(response.content)

            logger.info(f"精筛完成，选中 {len(result.get('selected_items', []))} 项")
            return result

        except Exception as e:
            logger.error(f"数据精筛失败：{e}")
            return self._fallback_refine(merged_data)

    def rewrite(
        self, structured_data: dict[str, Any], knowledge_graph: dict[str, Any], core_topic: str
    ) -> str:
        """重写数据。

        Args:
            structured_data: 结构化数据
            knowledge_graph: 知识图谱
            core_topic: 核心主题

        Returns:
            str: 重写后的内容（Markdown 格式）
        """
        logger.info("执行模型重写")

        prompt = format_prompt(
            self.prompts["model_rewriter"],
            structured_data=json.dumps(structured_data, ensure_ascii=False),
            knowledge_graph=json.dumps(knowledge_graph, ensure_ascii=False),
            credibility_info="{}",
        )

        try:
            response = self.model_provider.call(prompt=prompt, model="qwen3.5:7b")

            # 提取 Markdown 内容
            content = response.content

            # 尝试提取代码块中的内容
            import re

            md_match = re.search(r"```markdown\s*(.*?)\s*```", content, re.DOTALL)

            if md_match:
                content = md_match.group(1)

            logger.info("模型重写完成")
            return content

        except Exception as e:
            logger.error(f"模型重写失败：{e}")
            return self._fallback_rewrite(core_topic)

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """解析 JSON 响应。

        Args:
            content: 模型响应内容

        Returns:
            dict: 解析后的数据
        """
        import re

        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("JSON 解析失败")
            return {}

    def _fallback_refine(self, merged_data: str) -> dict[str, Any]:
        """备用精筛逻辑。

        Args:
            merged_data: 合并后的数据

        Returns:
            dict: 简化的精筛结果
        """
        # 简单分割数据
        sections = merged_data.split("## 来源")[:10]

        return {
            "selected_items": [
                {
                    "content": section,
                    "quality_score": 4.0,
                    "relevance_score": 4.0,
                    "credibility_score": 4.0,
                    "reason": "备用精筛：默认选中",
                }
                for section in sections
                if section.strip()
            ],
            "rejected_items": [],
        }

    def _fallback_rewrite(self, core_topic: str) -> str:
        """备用重写逻辑。

        Args:
            core_topic: 核心主题

        Returns:
            str: 简化的重写内容
        """
        return f"""# {core_topic}

## 概述

这是关于{core_topic}的知识文档。

## 核心内容

由于模型重写失败，这里是备用内容。建议检查模型配置后重新生成。

## 参考资料

- 来源数据已保存
"""

    def get_refined_data(self) -> dict[str, Any]:
        """获取精筛后的数据。

        Returns:
            dict: 精筛后的数据
        """
        return self.refined_data

    def reset(self) -> None:
        """重置精筛器状态。"""
        self.refined_data = {}
