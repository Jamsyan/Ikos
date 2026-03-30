"""知识图谱构建器 - 第三阶段核心组件."""

import json
from typing import Any
from loguru import logger


class KnowledgeGraphBuilder:
    """知识图谱构建器。
    
    在数据筛选过程中同步构建知识图谱。
    """
    
    def __init__(self):
        """初始化知识图谱构建器。"""
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self.node_index: dict[str, int] = {}
    
    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        description: str = "",
        properties: dict[str, Any] | None = None
    ) -> None:
        """添加节点。
        
        Args:
            node_id: 节点 ID
            label: 节点标签
            node_type: 节点类型（concept/person/event 等）
            description: 节点描述
            properties: 节点属性
        """
        node = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "description": description,
            "properties": properties or {}
        }
        
        if node_id not in self.node_index:
            self.nodes.append(node)
            self.node_index[node_id] = len(self.nodes) - 1
            logger.debug(f"添加节点：{node_id} ({label})")
        else:
            # 更新现有节点
            index = self.node_index[node_id]
            self.nodes[index] = node
            logger.debug(f"更新节点：{node_id} ({label})")
    
    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        properties: dict[str, Any] | None = None
    ) -> None:
        """添加边。
        
        Args:
            source: 源节点 ID
            target: 目标节点 ID
            relation: 关系类型
            properties: 边属性
        """
        edge = {
            "source": source,
            "target": target,
            "relation": relation,
            "properties": properties or {}
        }
        
        self.edges.append(edge)
        logger.debug(f"添加边：{source} -[{relation}]-> {target}")
    
    def build_from_data(
        self,
        data: list[dict[str, Any]],
        core_topic: str
    ) -> dict[str, Any]:
        """从数据构建知识图谱。
        
        Args:
            data: 数据列表
            core_topic: 核心主题
            
        Returns:
            dict: 构建的知识图谱
        """
        logger.info(f"从 {len(data)} 个数据项构建知识图谱")
        
        # 添加核心节点
        self.add_node(
            node_id="core",
            label=core_topic,
            node_type="core_concept",
            description=f"核心主题：{core_topic}"
        )
        
        # 从数据中提取实体
        prev_node_id = "core"
        for i, item in enumerate(data):
            title = item.get("title", "") or item.get("source", {}).get("title", "")
            content = item.get("content", "") or item.get("cleaned_content", "")
            
            if title:
                node_id = f"entity_{i}"
                
                # 确定实体类型
                entity_type = self._classify_entity(title, content)
                
                self.add_node(
                    node_id=node_id,
                    label=title,
                    node_type=entity_type,
                    description=content[:200] if content else ""
                )
                
                # 添加到核心节点的边
                self.add_edge(
                    source="core",
                    target=node_id,
                    relation="related_to"
                )
                
                # 如果有前一个节点，添加顺序关系
                if prev_node_id and prev_node_id != "core":
                    self.add_edge(
                        source=prev_node_id,
                        target=node_id,
                        relation="sequence"
                    )
                
                prev_node_id = node_id
        
        return self.get_graph()
    
    def _classify_entity(self, title: str, content: str) -> str:
        """分类实体类型。
        
        Args:
            title: 标题
            content: 内容
            
        Returns:
            str: 实体类型
        """
        title_lower = title.lower()
        content_lower = content.lower()
        
        # 人物
        if any(word in title_lower for word in ["提出", "发现", "发明"]):
            return "person"
        
        # 事件
        if any(word in title_lower for word in ["历史", "发展", "演变"]):
            return "event"
        
        # 概念
        if any(word in content_lower for word in ["定义", "是指", "称为"]):
            return "concept"
        
        # 应用
        if any(word in title_lower for word in ["应用", "用途", "场景"]):
            return "application"
        
        # 默认为相关概念
        return "related_concept"
    
    def get_graph(self) -> dict[str, Any]:
        """获取知识图谱。
        
        Returns:
            dict: 知识图谱
        """
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "created_at": "2026-03-31"
            }
        }
    
    def export_json(self, filepath: str) -> None:
        """导出为 JSON 文件。
        
        Args:
            filepath: 输出文件路径
        """
        graph = self.get_graph()
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识图谱已导出到：{filepath}")
    
    def reset(self) -> None:
        """重置构建器状态。"""
        self.nodes = []
        self.edges = []
        self.node_index = {}
