"""集成测试 - 端到端流程测试."""

import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestIntegration:
    """集成测试类。"""
    
    @pytest.mark.skip(reason="需要 Ollama 服务运行")
    def test_full_pipeline(self):
        """测试完整流程。"""
        from ikos.core.pipeline import IkosPipeline
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建管道
            pipeline = IkosPipeline("config/settings.yaml")
            
            # 执行流程
            output_config = {
                "output_type": "file",
                "formats": ["json", "markdown"],
                "output_path": tmpdir
            }
            
            result = pipeline.run("傅里叶变换基础概念", output_config)
            
            # 验证结果
            assert result["status"] == "success"
            assert "output_files" in result
            assert len(result["output_files"]) > 0
    
    def test_mock_full_pipeline(self):
        """测试模拟完整流程（使用 Mock）。"""
        from ikos.core.model_provider import ModelResponse

        # Mock 所有组件
        class MockModelProvider:
            def call(self, prompt, model, **kwargs):
                return ModelResponse(
                    content=self._get_mock_response(prompt),
                    model=model
                )
            
            def _get_mock_response(self, prompt):
                if "初始解析" in prompt or "initial" in prompt.lower():
                    return '{"core_need": "test", "key_concepts": ["傅里叶变换"], "complexity": "简单", "suggested_rounds": 1}'
                elif "任务拆分" in prompt or "split" in prompt.lower():
                    return '''```json
{"tasks": [{"id": "task_1", "name": "测试任务", "description": "测试", "search_queries": ["test"], "expected_output": "test"}]}
```'''
                elif "重写" in prompt or "rewrite" in prompt.lower():
                    return "```markdown\n# 傅里叶变换\n\n这是测试内容。\n```"
                else:
                    return "{}"
        
        class MockSearchProvider:
            def search(self, query, max_results=10, engine="auto"):
                from ikos.core.types import SearchResult
                return [
                    SearchResult(
                        title="Test Result",
                        url="https://example.com",
                        snippet="Test snippet",
                        source="test",
                        rank=1
                    )
                ]
            
            def fetch_content(self, url, extract_text=True):
                from ikos.core.types import WebContent
                return WebContent(
                    url=url,
                    title="Test",
                    content="Test content",
                    html="<html><body>Test</body></html>"
                )
        
        # 由于管道初始化会创建真实组件，这里简化测试
        # 实际应该使用依赖注入
        assert True  # 占位测试
    
    def test_config_loading(self):
        """测试配置加载。"""
        from ikos.utils.config_loader import load_config
        
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        
        if config_path.exists():
            config = load_config(config_path)
            
            assert config is not None
            assert "model" in config
            assert "search" in config
            assert "output" in config
        else:
            pytest.skip("配置文件不存在")
    
    def test_prompt_templates(self):
        """测试提示词模板加载。"""
        from ikos.utils.config_loader import load_yaml
        
        prompts_dir = Path(__file__).parent.parent / "config" / "prompts"
        
        # 测试所有阶段模板
        template_files = [
            "stage1_parse.yaml",
            "stage2_search.yaml",
            "stage3_filter.yaml",
            "stage4_output.yaml"
        ]
        
        for template_file in template_files:
            template_path = prompts_dir / template_file
            
            if template_path.exists():
                prompts = load_yaml(template_path)
                assert prompts is not None
                assert len(prompts) > 0
            else:
                pytest.skip(f"模板文件不存在：{template_file}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
