"""核心接口测试."""

import pytest


def test_import_model_provider():
    """测试 ModelProvider 导入."""
    from ikos.core import ModelProvider

    assert ModelProvider is not None


def test_import_search_provider():
    """测试 SearchProvider 导入."""
    from ikos.core import SearchProvider

    assert SearchProvider is not None


@pytest.mark.skip(reason="待实现")
def test_model_provider_call():
    """测试模型调用（待实现）."""
    pass


@pytest.mark.skip(reason="待实现")
def test_search_provider_search():
    """测试搜索功能（待实现）."""
    pass
