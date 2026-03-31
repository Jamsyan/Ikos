"""Ikos 管道测试."""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPipeline:
    """测试 Ikos 管道。"""
    
    def test_pipeline_initialization(self):
        """测试管道初始化。"""
        from ikos.core.pipeline import IkosPipeline

        # 创建管道（需要 Ollama 服务运行）
        # 如果 Ollama 未运行，这个测试会失败
        try:
            pipeline = IkosPipeline("config/settings.yaml")
            assert pipeline is not None
            assert pipeline.model_provider is not None
            assert pipeline.search_provider is not None
        except Exception as e:
            # 如果服务未运行，跳过测试
            pytest.skip(f"Ollama 服务未运行：{e}")
    
    def test_stage1_parser_initialization(self):
        """测试第一阶段解析器初始化。"""
        from ikos.core import OllamaProvider
        from ikos.stage1_requirement.parser import RequirementParser

        # 使用 mock provider
        class MockProvider:
            def call(self, prompt, model, **kwargs):
                from ikos.core.model_provider import ModelResponse
                return ModelResponse(
                    content='{"core_need": "test", "key_concepts": ["test"], "complexity": "简单", "suggested_rounds": 1}',
                    model=model
                )
        
        parser = RequirementParser(MockProvider())
        assert parser is not None
        assert parser.max_rounds == 10
    
    def test_stage1_parser_parse(self):
        """测试需求解析功能。"""
        from ikos.stage1_requirement.parser import RequirementParser
        
        class MockProvider:
            def call(self, prompt, model, **kwargs):
                from ikos.core.model_provider import ModelResponse
                return ModelResponse(
                    content='{"core_need": "了解傅里叶变换", "key_concepts": ["傅里叶变换"], "complexity": "中等", "suggested_rounds": 3}',
                    model=model
                )
        
        parser = RequirementParser(MockProvider())
        result = parser.parse("我想知道傅里叶变换的数学知识")
        
        assert result is not None
        assert "core_need" in result
        assert result["core_need"] == "了解傅里叶变换"
    
    def test_stage2_task_splitter(self):
        """测试任务拆分器。"""
        from ikos.stage2_search.task_splitter import TaskSplitter
        
        class MockProvider:
            def call(self, prompt, model, **kwargs):
                from ikos.core.model_provider import ModelResponse
                return ModelResponse(
                    content='''```json
{
    "tasks": [
        {
            "id": "task_1",
            "name": "基本概念",
            "description": "检索基本概念",
            "search_queries": ["傅里叶变换 定义"],
            "expected_output": "概念列表"
        }
    ]
}
```''',
                    model=model
                )
        
        splitter = TaskSplitter(MockProvider())
        result = splitter.split("检索傅里叶变换知识", "傅里叶变换")
        
        assert result is not None
        assert "tasks" in result
        assert len(result["tasks"]) > 0
    
    def test_stage3_initial_filter(self):
        """测试初筛过滤器。"""
        from ikos.stage3_filter.initial_filter import InitialFilter
        
        class MockProvider:
            def call(self, prompt, model, **kwargs):
                from ikos.core.model_provider import ModelResponse
                return ModelResponse(content="", model=model)
        
        filter = InitialFilter(MockProvider())
        
        # 测试 HTML 过滤
        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        result = filter.filter_html(html, "test")
        
        assert result is not None
        assert "cleaned_content" in result
        assert "Content" in result["cleaned_content"]
    
    def test_stage3_knowledge_graph_builder(self):
        """测试知识图谱构建器。"""
        from ikos.stage3_filter.knowledge_graph import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder()
        
        # 添加节点
        builder.add_node("core", "傅里叶变换", "concept", "核心概念")
        builder.add_node("node1", "傅里叶", "person", "数学家")
        
        # 添加边
        builder.add_edge("core", "node1", "proposed_by")
        
        graph = builder.get_graph()
        
        assert graph is not None
        assert len(graph["nodes"]) == 2
        assert len(graph["edges"]) == 1
    
    def test_stage4_file_outputter(self):
        """测试文件输出器。"""
        import tempfile

        from ikos.stage4_output.file_output import FileOutputter
        
        outputter = FileOutputter()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试知识图谱导出
            kg = {"nodes": [], "edges": [], "metadata": {}}
            result = outputter.export_knowledge_graph(kg, tmpdir)
            
            assert result is not None
            assert result["filename"] == "knowledge_graph.json"
            
            # 验证文件存在
            output_path = Path(tmpdir) / "knowledge_graph.json"
            assert output_path.exists()
    
    def test_utils_config_loader(self):
        """测试配置加载器。"""
        from ikos.utils.config_loader import load_yaml

        # 测试加载存在的配置
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        if config_path.exists():
            config = load_yaml(config_path)
            assert config is not None
            assert isinstance(config, dict)
        else:
            pytest.skip("配置文件不存在")
    
    def test_utils_logger(self):
        """测试日志配置。"""
        import tempfile

        from ikos.utils.logger import setup_logger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logger(log_file=str(log_file), level="INFO")
            
            from loguru import logger
            logger.info("Test log message")
            
            # 验证日志文件存在
            assert log_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
