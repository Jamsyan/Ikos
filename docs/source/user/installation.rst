安装指南
========

系统要求
--------

- Python 3.13 或更高版本
- 8GB+ RAM（推荐 16GB）
- 20GB 可用磁盘空间

快速安装
--------

1. **安装 UV 包管理器**（如果尚未安装）：

   .. code-block:: bash

      curl -LsSf https://astral.sh/uv/install.sh | sh

   Windows:

   .. code-block:: powershell

      powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

2. **克隆仓库**：

   .. code-block:: bash

      git clone https://github.com/jamsyan/Ikos.git
      cd Ikos

3. **创建虚拟环境并安装依赖**：

   .. code-block:: bash

      uv venv
      source .venv/bin/activate  # Linux/macOS
      .venv\Scripts\activate     # Windows

      uv pip install -e ".[dev]"

4. **安装 Playwright 浏览器**：

   .. code-block:: bash

      playwright install

5. **验证安装**：

   .. code-block:: bash

      ikos --version

Ollama 安装（可选）
------------------

如果需要使用本地模型：

1. **安装 Ollama**：

   访问 https://ollama.ai 下载安装

2. **下载模型**：

   .. code-block:: bash

      ollama pull qwen3.5:7b
      ollama pull deepseek-r1:7b

数据库安装（可选）
----------------

**Chroma（向量数据库）**：

已包含在 Python 依赖中，无需额外安装。

**Neo4j（图数据库）**：

1. 使用 Docker：

   .. code-block:: bash

      docker run -d \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/password \
        neo4j:latest

2. 或访问 https://neo4j.com/download 下载安装

验证安装
--------

运行测试套件：

.. code-block:: bash

   pytest

检查配置：

.. code-block:: bash

   ikos config check

下一步
------

安装完成后，请参阅 :doc:`quickstart` 开始使用 Ikos。
