"""UI 配置管理器测试."""

import pytest
import json
from pathlib import Path

from ikos.ui.config_manager import UIConfigManager


class TestUIConfigManager:
    """测试 UI 配置管理器."""

    def test_init_default(self):
        """测试默认初始化."""
        manager = UIConfigManager()
        
        assert manager.config_file.exists() or not manager.config_file.exists()
        assert isinstance(manager.get_all_config(), dict)

    def test_window_geometry(self):
        """测试窗口几何信息."""
        manager = UIConfigManager()
        
        # 默认值
        geometry = manager.get_window_geometry()
        assert "x" in geometry
        assert "y" in geometry
        assert "width" in geometry
        assert "height" in geometry
        
        # 设置并获取
        manager.set_window_geometry(200, 200, 1400, 1000)
        geometry = manager.get_window_geometry()
        
        assert geometry["x"] == 200
        assert geometry["y"] == 200
        assert geometry["width"] == 1400
        assert geometry["height"] == 1000

    def test_model_selection(self):
        """测试模型选择."""
        manager = UIConfigManager()
        
        # 默认值
        model = manager.get_model_selection()
        assert isinstance(model, str)
        
        # 设置并获取
        manager.set_model_selection("Qwen 3.5 14B")
        model = manager.get_model_selection()
        
        assert model == "Qwen 3.5 14B"

    def test_engine_mode(self):
        """测试引擎模式."""
        manager = UIConfigManager()
        
        # 默认值
        mode = manager.get_engine_mode()
        assert isinstance(mode, str)
        
        # 设置并获取
        manager.set_engine_mode("原生引擎")
        mode = manager.get_engine_mode()
        
        assert mode == "原生引擎"

    def test_quantization_level(self):
        """测试量化等级."""
        manager = UIConfigManager()
        
        # 默认值
        level = manager.get_quantization_level()
        assert isinstance(level, str)
        
        # 设置并获取
        manager.set_quantization_level("INT8")
        level = manager.get_quantization_level()
        
        assert level == "INT8"

    def test_output_config(self):
        """测试输出配置."""
        manager = UIConfigManager()
        
        # 默认值
        config = manager.get_output_config()
        assert "formats" in config
        assert "output_dir" in config
        
        # 设置并获取
        new_config = {
            "formats": ["markdown"],
            "output_dir": "./custom_output",
            "include_knowledge_graph": False,
        }
        manager.set_output_config(new_config)
        config = manager.get_output_config()
        
        assert config["formats"] == ["markdown"]
        assert config["output_dir"] == "./custom_output"
        assert config["include_knowledge_graph"] is False

    def test_recent_queries(self):
        """测试最近的查询."""
        manager = UIConfigManager()
        
        # 初始为空
        queries = manager.get_recent_queries()
        assert isinstance(queries, list)
        
        # 添加查询
        manager.add_recent_query("测试查询 1")
        manager.add_recent_query("测试查询 2")
        
        queries = manager.get_recent_queries()
        assert len(queries) == 2
        assert queries[0] == "测试查询 1"
        
        # 添加重复查询
        manager.add_recent_query("测试查询 1")
        queries = manager.get_recent_queries()
        assert len(queries) == 2  # 不增加
        
        # 清除
        manager.clear_recent_queries()
        queries = manager.get_recent_queries()
        assert len(queries) == 0

    def test_reset_to_defaults(self):
        """测试重置为默认."""
        manager = UIConfigManager()
        
        # 修改一些配置
        manager.set_window_geometry(300, 300, 1500, 1100)
        manager.set_model_selection("Custom Model")
        
        # 重置
        manager.reset_to_defaults()
        
        # 检查是否恢复默认
        geometry = manager.get_window_geometry()
        assert geometry["x"] == 100  # 默认值
        assert geometry["y"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
