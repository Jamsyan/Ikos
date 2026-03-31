"""测试模型源选择器。"""

import sys
from pathlib import Path

import pytest

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
        from ikos.utils.model_source import (get_model_source, is_huggingface,
                                             is_modelscope)

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
        import tempfile

        from ikos.utils.model_downloader import ModelDownloader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir)
            
            assert downloader.cache_dir == Path(tmpdir)
            assert downloader.cache_dir.exists()
    
    def test_downloader_get_model_path(self):
        """测试获取模型路径。"""
        import tempfile

        from ikos.utils.model_downloader import ModelDownloader
        
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir)
            
            # 不存在的模型
            path = downloader.get_model_path("test/model")
            assert path is None
    
    def test_download_function(self):
        """测试便捷下载函数。"""
        import tempfile

        from ikos.utils.model_downloader import download_model
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 注意：这个测试需要网络连接，可能会失败
            # 实际使用：download_model("damo/nlp_csanmt_translationzh2en")
            pass

    def test_resolve_revision_by_source(self):
        """应按来源修正默认 revision。"""
        import tempfile

        from ikos.utils.model_downloader import ModelDownloader

        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir)

            assert downloader._resolve_revision("modelscope", "main") == "master"
            assert downloader._resolve_revision("huggingface", "master") == "main"
            assert downloader._resolve_revision("modelscope", "feature-branch") == "feature-branch"

    def test_modelscope_download_uses_supported_pattern_args(self, monkeypatch):
        """ModelScope 下载应使用 allow_patterns / ignore_patterns。"""
        import sys
        import tempfile
        import types
        from pathlib import Path

        from ikos.utils.model_downloader import ModelDownloader

        captured_kwargs = {}

        def fake_snapshot_download(**kwargs):
            captured_kwargs.update(kwargs)
            target = Path(kwargs["cache_dir"]) / "Qwen" / "Qwen2.5-7B-Instruct" / kwargs["revision"]
            target.mkdir(parents=True, exist_ok=True)
            (target / "config.json").write_text("{}", encoding="utf-8")
            (target / "model.safetensors").write_text("weights", encoding="utf-8")
            return str(target)

        fake_module = types.SimpleNamespace(snapshot_download=fake_snapshot_download)
        monkeypatch.setitem(sys.modules, "modelscope", fake_module)

        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = ModelDownloader(cache_dir=tmpdir, preferred_source="modelscope")
            downloader.download(
                model_id="Qwen/Qwen2.5-7B-Instruct",
                revision="main",
                allow_patterns=["*.json"],
                ignore_patterns=["*.bin"],
            )

        assert captured_kwargs["revision"] == "master"
        assert captured_kwargs["allow_patterns"] == ["*.json"]
        assert captured_kwargs["ignore_patterns"] == ["*.bin"]
        assert "include" not in captured_kwargs
        assert "exclude" not in captured_kwargs


class TestDownloadLogRewrite:
    """测试下载日志改写。"""

    def test_download_log_rewrite(self):
        """下载日志应改写为更适合 UI 展示的文本。"""
        from ikos.ui.components.model_manager import ModelDownloadThread

        assert ModelDownloadThread._rewrite_download_message("模型下载器已初始化") is None
        assert (
            ModelDownloadThread._rewrite_download_message("使用模型源：modelscope")
            == "本次下载将使用：魔塔社区"
        )
        assert (
            ModelDownloadThread._rewrite_download_message("开始下载模型：Qwen/Qwen2.5-7B-Instruct")
            == "准备下载模型：Qwen/Qwen2.5-7B-Instruct"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
