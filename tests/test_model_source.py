"""测试模型源选择器。"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelSourceSelector:
    """测试模型源选择器。"""
    
    def test_selector_initialization(self):
        """测试选择器初始化。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        # 默认 auto
        selector = ModelSourceSelector()
        assert selector.preferred == "auto"
        
        # 指定魔塔
        selector_ms = ModelSourceSelector(preferred="modelscope")
        assert selector_ms.preferred == "modelscope"
        
        # 指定 Hugging Face
        selector_hf = ModelSourceSelector(preferred="huggingface")
        assert selector_hf.preferred == "huggingface"
    
    def test_selector_detect_auto(self):
        """测试自动检测。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        selector = ModelSourceSelector(preferred="auto")
        result = selector.detect()
        
        # 应该返回 modelscope 或 huggingface
        assert result in ["modelscope", "huggingface"]
    
    def test_selector_detect_preferred(self):
        """测试使用首选源。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        # 指定魔塔
        selector = ModelSourceSelector(preferred="modelscope")
        result = selector.detect()
        assert result == "modelscope"
        
        # 指定 Hugging Face
        selector = ModelSourceSelector(preferred="huggingface")
        result = selector.detect()
        assert result == "huggingface"
    
    def test_selector_cache(self):
        """测试缓存机制。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        selector = ModelSourceSelector(preferred="auto")
        
        # 第一次检测
        result1 = selector.detect()
        
        # 第二次应该使用缓存
        result2 = selector.detect()
        assert result1 == result2
    
    def test_selector_reset_cache(self):
        """测试重置缓存。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        selector = ModelSourceSelector(preferred="auto")
        
        # 检测并缓存
        result1 = selector.detect()
        
        # 重置缓存
        selector.reset_cache()
        
        # 缓存已清除
        assert selector._cached_result is None
    
    def test_convenience_functions(self):
        """测试便捷函数。"""
        from ikos.utils.model_source import (
            get_model_source,
            is_modelscope,
            is_huggingface
        )
        
        # get_model_source
        source = get_model_source(preferred="auto")
        assert source in ["modelscope", "huggingface"]
        
        # is_modelscope / is_huggingface
        if is_modelscope():
            assert not is_huggingface()
        else:
            assert is_huggingface()
    
    def test_get_download_url(self):
        """测试获取下载 URL。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        selector = ModelSourceSelector(preferred="modelscope")
        
        # 魔塔 URL
        url = selector.get_download_url("damo/nlp_csanmt_translationzh2en")
        assert "modelscope.cn" in url
        
        # Hugging Face URL
        selector_hf = ModelSourceSelector(preferred="huggingface")
        url_hf = selector_hf.get_download_url("facebook/bart-base")
        assert "huggingface.co" in url_hf
    
    def test_get_api_endpoint(self):
        """测试获取 API 端点。"""
        from ikos.utils.model_source import ModelSourceSelector
        
        # 魔塔端点
        selector = ModelSourceSelector(preferred="modelscope")
        endpoint = selector.get_api_endpoint()
        assert "modelscope.cn" in endpoint
        
        # Hugging Face 端点
        selector_hf = ModelSourceSelector(preferred="huggingface")
        endpoint_hf = selector_hf.get_api_endpoint()
        assert "huggingface.co" in endpoint_hf


class TestModelDownloader:
    """测试模型下载器。"""
    
    def test_downloader_initialization(self):
        """测试下载器初始化。"""
        from ikos.utils.model_downloader import ModelDownloader
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir)
            
            assert downloader.cache_dir == Path(tmpdir)
            assert downloader.cache_dir.exists()
    
    def test_downloader_get_model_path(self):
        """测试获取模型路径。"""
        from ikos.utils.model_downloader import ModelDownloader
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir)
            
            # 不存在的模型
            path = downloader.get_model_path("test/model")
            assert path is None
    
    def test_download_function(self):
        """测试便捷下载函数。"""
        from ikos.utils.model_downloader import download_model
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 注意：这个测试需要网络连接，可能会失败
            # 实际使用：download_model("damo/nlp_csanmt_translationzh2en")
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
