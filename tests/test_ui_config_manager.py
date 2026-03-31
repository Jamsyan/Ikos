"""测试 UI 配置管理器。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_download_source_roundtrip(tmp_path):
    """下载源配置应能写入并恢复。"""
    from ikos.ui.config_manager import UIConfigManager

    config_path = tmp_path / "ui_config.json"
    manager = UIConfigManager(config_path)

    assert manager.get_download_source() == "auto"

    manager.set_download_source("modelscope")

    restored = UIConfigManager(config_path)
    assert restored.get_download_source() == "modelscope"
