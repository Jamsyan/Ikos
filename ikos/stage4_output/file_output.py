"""文件输出器 - 第四阶段核心组件."""

import json
from pathlib import Path
from typing import Any
from loguru import logger


class FileOutputter:
    """文件输出器。
    
    将知识产物输出为各种文件格式。
    """
    
    def __init__(self):
        """初始化文件输出器。"""
        self.output_files: list[dict[str, Any]] = []
    
    def export_knowledge_graph(
        self,
        knowledge_graph: dict[str, Any],
        output_dir: str,
        format: str = "json"
    ) -> dict[str, Any]:
        """导出知识图谱。
        
        Args:
            knowledge_graph: 知识图谱数据
            output_dir: 输出目录
            format: 输出格式
            
        Returns:
            dict: 导出结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            filepath = output_path / "knowledge_graph.json"
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(knowledge_graph, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识图谱已导出：{filepath}")
            
            return {
                "filename": "knowledge_graph.json",
                "format": "json",
                "path": str(filepath),
                "type": "knowledge_graph"
            }
        
        else:
            logger.warning(f"不支持的知识图谱格式：{format}")
            return {}
    
    def export_structured_data(
        self,
        structured_data: dict[str, Any],
        output_dir: str,
        format: str = "json"
    ) -> dict[str, Any]:
        """导出结构化数据。
        
        Args:
            structured_data: 结构化数据
            output_dir: 输出目录
            format: 输出格式
            
        Returns:
            dict: 导出结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            filepath = output_path / "structured_data.json"
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结构化数据已导出：{filepath}")
            
            return {
                "filename": "structured_data.json",
                "format": "json",
                "path": str(filepath),
                "type": "structured_data"
            }
        
        else:
            logger.warning(f"不支持的结构化数据格式：{format}")
            return {}
    
    def export_document(
        self,
        content: str,
        output_dir: str,
        format: str = "markdown",
        filename: str | None = None
    ) -> dict[str, Any]:
        """导出文档。
        
        Args:
            content: 文档内容
            output_dir: 输出目录
            format: 输出格式
            filename: 文件名
            
        Returns:
            dict: 导出结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            if filename is None:
                filename = "output.md"
            
            filepath = output_path / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"文档已导出：{filepath}")
            
            return {
                "filename": filename,
                "format": "markdown",
                "path": str(filepath),
                "type": "document"
            }
        
        elif format == "pdf":
            # 简化实现：保存为文本，实际应该转换为 PDF
            if filename is None:
                filename = "output.txt"
            
            filepath = output_path / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"PDF 文本已保存：{filepath}（需要转换为 PDF）")
            
            return {
                "filename": filename,
                "format": "pdf_text",
                "path": str(filepath),
                "type": "document",
                "note": "需要额外工具转换为 PDF"
            }
        
        else:
            logger.warning(f"不支持的文档格式：{format}")
            return {}
    
    def export_all(
        self,
        knowledge_graph: dict[str, Any],
        structured_data: dict[str, Any],
        rewritten_content: str,
        output_dir: str,
        formats: list[str]
    ) -> list[dict[str, Any]]:
        """导出所有文件。
        
        Args:
            knowledge_graph: 知识图谱
            structured_data: 结构化数据
            rewritten_content: 重写后的内容
            output_dir: 输出目录
            formats: 输出格式列表
            
        Returns:
            list: 所有导出文件的信息
        """
        files = []
        
        # 导出知识图谱
        kg_file = self.export_knowledge_graph(knowledge_graph, output_dir)
        if kg_file:
            files.append(kg_file)
        
        # 导出结构化数据
        data_file = self.export_structured_data(structured_data, output_dir)
        if data_file:
            files.append(data_file)
        
        # 导出文档
        for fmt in formats:
            doc_file = self.export_document(rewritten_content, output_dir, fmt)
            if doc_file:
                files.append(doc_file)
        
        self.output_files.extend(files)
        return files
    
    def get_output_files(self) -> list[dict[str, Any]]:
        """获取所有输出文件。
        
        Returns:
            list: 输出文件列表
        """
        return self.output_files
    
    def reset(self) -> None:
        """重置输出器状态。"""
        self.output_files = []
