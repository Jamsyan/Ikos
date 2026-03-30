# Sphinx 配置文件
# 用于自动生成 API 文档

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir / "src"))

# 项目信息
project = "Ikos"
copyright = "2026, jamsyan"
author = "jamsyan"
release = "0.1.0"

# 扩展配置
extensions = [
    "sphinx.ext.autodoc",      # 自动生成 API 文档
    "sphinx.ext.autosummary",  # 自动生成摘要
    "sphinx.ext.napoleon",     # 支持 Google/NumPy 风格文档字符串
    "sphinx.ext.viewcode",     # 在文档中显示源代码
    "sphinx.ext.intersphinx",  # 链接到其他项目的文档
    "myst_parser",             # 支持 Markdown 格式
    "sphinx_autobuild",        # 实时预览
]

# Markdown 支持
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
]

# Autodoc 配置
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Autosummary 配置
autosummary_generate = True

# Intersphinx 配置
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# 模板路径
templates_path = ["_templates"]

# 排除模式
exclude_patterns = []

# HTML 主题
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# 语言
language = "zh_CN"

# 主文件
master_doc = "index"
