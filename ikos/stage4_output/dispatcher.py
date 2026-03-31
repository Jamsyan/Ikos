"""输出分流器 - 第四阶段核心组件."""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from ikos.core import ModelProvider
from ikos.utils.config_loader import load_yaml


class OutputDispatcher:
    """输出分流器。
    
    根据用户配置将结构化数据分流到不同输出路径。
    """
    
    def __init__(self, model_provider: ModelProvider, config_path: str | None = None):
        """初始化输出分流器。
        
        Args:
            model_provider: 模型提供者
            config_path: 提示词配置文件路径
        """
        self.model_provider = model_provider
        
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "prompts" / "stage4_output.yaml"
        
        self.prompts = load_yaml(config_path)
        self.output_config: dict[str, Any] = {}
    
    def configure(self, user_config: dict[str, Any]) -> dict[str, Any]:
        """配置输出参数。
        
        Args:
            user_config: 用户配置
            
        Returns:
            dict: 解析后的配置
        """
        logger.info("解析输出配置")
        
        available_formats = ["json", "markdown", "pdf"]
        
        prompt = self.prompts["output_config"].format(
            user_config=json.dumps(user_config, ensure_ascii=False),
            available_formats=available_formats
        )
        
        try:
            response = self.model_provider.call(
                prompt=prompt,
                model="qwen3.5:7b"
            )
            
            result = self._parse_json_response(response.content)
            self.output_config = result
            
            logger.info(f"输出配置解析完成：{result.get('output_type', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"输出配置解析失败：{e}")
            return self._fallback_config(user_config)
    
    def dispatch(
        self,
        structured_data: dict[str, Any],
        knowledge_graph: dict[str, Any],
        rewritten_content: str
    ) -> dict[str, Any]:
        """执行输出分流。
        
        Args:
            structured_data: 结构化数据
            knowledge_graph: 知识图谱
            rewritten_content: 重写后的内容
            
        Returns:
            dict: 分流结果
        """
        logger.info("执行输出分流")
        
        output_type = self.output_config.get("output_type", "file")
        formats = self.output_config.get("formats", ["json", "markdown"])
        
        results = {
            "files": [],
            "database_records": 0,
            "status": "success"
        }
        
        # 文件输出
        if output_type in ["file", "both"]:
            file_results = self._dispatch_files(
                structured_data,
                knowledge_graph,
                rewritten_content,
                formats
            )
            results["files"].extend(file_results)
        
        # 数据库输出
        if output_type in ["database", "both"]:
            db_config = self.output_config.get("database_config", {})
            if db_config:
                db_results = self._dispatch_database(
                    structured_data,
                    knowledge_graph,
                    db_config
                )
                results["database_records"] = db_results.get("record_count", 0)
        
        return results
    
    def _dispatch_files(
        self,
        structured_data: dict[str, Any],
        knowledge_graph: dict[str, Any],
        rewritten_content: str,
        formats: list[str]
    ) -> list[dict[str, Any]]:
        """执行文件输出分流。
        
        Args:
            structured_data: 结构化数据
            knowledge_graph: 知识图谱
            rewritten_content: 重写后的内容
            formats: 输出格式列表
            
        Returns:
            list: 文件输出结果
        """
        from .file_output import FileOutputter
        
        outputter = FileOutputter()
        output_dir = self.output_config.get("output_path", "./data/output")
        
        files = []
        
        # 知识图谱输出
        kg_file = outputter.export_knowledge_graph(
            knowledge_graph,
            output_dir,
            format="json"
        )
        files.append(kg_file)
        
        # 结构化数据输出
        data_file = outputter.export_structured_data(
            structured_data,
            output_dir,
            format="json"
        )
        files.append(data_file)
        
        # 文档输出
        for fmt in formats:
            if fmt == "markdown":
                doc_file = outputter.export_document(
                    rewritten_content,
                    output_dir,
                    format="markdown"
                )
                files.append(doc_file)
        
        return files
    
    def _dispatch_database(
        self,
        structured_data: dict[str, Any],
        knowledge_graph: dict[str, Any],
        db_config: dict[str, Any]
    ) -> dict[str, Any]:
        """执行数据库输出分流。
        
        Args:
            structured_data: 结构化数据
            knowledge_graph: 知识图谱
            db_config: 数据库配置
            
        Returns:
            dict: 数据库输出结果
        """
        from .db_output import DatabaseOutputter
        
        outputter = DatabaseOutputter(db_config)
        
        # 根据数据库类型输出
        db_type = db_config.get("type", "vector")
        
        if db_type == "graph":
            result = outputter.export_to_graph_db(knowledge_graph)
        elif db_type == "vector":
            result = outputter.export_to_vector_db(structured_data)
        else:
            result = outputter.export_to_relational_db(structured_data)
        
        return result
    
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
    
    def _fallback_config(self, user_config: dict[str, Any]) -> dict[str, Any]:
        """备用配置解析。
        
        Args:
            user_config: 用户配置
            
        Returns:
            dict: 简化的配置
        """
        return {
            "output_type": "file",
            "formats": ["json", "markdown"],
            "output_path": "./data/output",
            "template": "default",
            "content_scope": "all",
            "include_knowledge_graph": True
        }
    
    def reset(self) -> None:
        """重置分流器状态。"""
        self.output_config = {}
