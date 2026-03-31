"""测试模型缓存管理器。"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_list_cached_models_from_metadata(tmp_path):
    """应能通过元数据列出缓存模型。"""
    from ikos.utils.cache_manager import ModelCacheManager

    manager = ModelCacheManager(tmp_path)
    model_path = manager.get_model_path(
        "Qwen/Qwen2.5-7B-Instruct",
        revision="main",
        source="modelscope",
        create=True,
    )
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    (model_path / "model.safetensors").write_text("weights", encoding="utf-8")

    manager.save_metadata(
        model_path=model_path,
        model_id="Qwen/Qwen2.5-7B-Instruct",
        revision="main",
        source="modelscope",
        download_info={"source": "modelscope"},
    )

    cached_models = manager.list_cached_models()
    assert len(cached_models) == 1
    assert cached_models[0]["name"] == "Qwen/Qwen2.5-7B-Instruct"
    assert cached_models[0]["source"] == "modelscope"
    assert Path(cached_models[0]["path"]) == model_path


def test_find_model_path_without_revision(tmp_path):
    """不指定 revision 时应返回已缓存路径。"""
    from ikos.utils.cache_manager import ModelCacheManager

    manager = ModelCacheManager(tmp_path)
    model_path = manager.get_model_path(
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        revision="main",
        source="huggingface",
        create=True,
    )
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    (model_path / "model.safetensors").write_text("weights", encoding="utf-8")

    manager.save_metadata(
        model_path=model_path,
        model_id="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        revision="main",
        source="huggingface",
        download_info={"source": "huggingface"},
    )

    assert (
        manager.find_model_path(
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            revision=None,
        )
        == model_path
    )
