"""测试 QML UI 是否能正常启动。"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_qml_imports():
    """测试 QML 相关导入是否正常。"""
    print("测试导入...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("[OK] PyQt6.QtWidgets 导入成功")
    except ImportError as e:
        print(f"[FAIL] PyQt6 导入失败：{e}")
        return False
    
    try:
        from PyQt6.QtQml import QQmlApplicationEngine
        print("[OK] PyQt6.QtQml 导入成功")
    except ImportError as e:
        print(f"[FAIL] QtQml 导入失败：{e}")
        return False
    
    try:
        from ikos.ui.qml_bridge import PythonBridge
        print("[OK] PythonBridge 导入成功")
    except ImportError as e:
        print(f"[FAIL] PythonBridge 导入失败：{e}")
        return False
    
    try:
        from ikos.ui.main_window_qml import MainWindowQML
        print("[OK] MainWindowQML 导入成功")
    except ImportError as e:
        print(f"[FAIL] MainWindowQML 导入失败：{e}")
        return False
    
    return True


def test_qml_files():
    """测试 QML 文件是否存在。"""
    print("\n测试 QML 文件...")
    
    qml_dir = Path(__file__).parent.parent / "ikos" / "ui" / "qml"
    
    required_files = [
        "Main.qml",
        "InputPanel.qml",
        "OutputPanel.qml",
        "Theme.qml"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = qml_dir / file
        if file_path.exists():
            print(f"[OK] {file} 存在")
        else:
            print(f"[FAIL] {file} 不存在")
            all_exist = False
    
    return all_exist


def test_ui_launch():
    """测试 UI 启动（不阻塞）。"""
    print("\n测试 UI 启动...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from ikos.ui.main_window_qml import MainWindowQML
        
        # 创建应用（不运行事件循环）
        app = QApplication.instance() or QApplication(sys.argv)
        print("[OK] QApplication 创建成功")
        
        # 创建主窗口（不显示）
        window = MainWindowQML(app)
        print("[OK] MainWindowQML 创建成功")
        
        # 检查引擎是否加载
        if window.engine:
            print("[OK] QML 引擎加载成功")
        else:
            print("[FAIL] QML 引擎加载失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] UI 启动测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Ikos QML UI 测试")
    print("=" * 60)
    
    # 测试导入
    if not test_qml_imports():
        print("\n[FAIL] 导入测试失败，请检查 PyQt6 安装")
        sys.exit(1)
    
    # 测试文件
    if not test_qml_files():
        print("\n[FAIL] QML 文件检查失败")
        sys.exit(1)
    
    # 测试启动
    if not test_ui_launch():
        print("\n[FAIL] UI 启动测试失败")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 所有测试通过！QML UI 可以正常运行")
    print("=" * 60)
    print("\n提示：运行以下命令启动 UI：")
    print("  ikos --ui")
    print("  或")
    print("  python -c 'from ikos.ui import run_ui; run_ui()'")
