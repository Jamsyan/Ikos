快速开始
========

基本使用
--------

1. **启动 Ikos**：

   .. code-block:: bash

      ikos

2. **输入你的问题**：

   例如："我想知道傅里叶变换的数学知识"

3. **等待处理完成**：

   Ikos 会自动执行四个阶段：
   - 需求解析
   - 智能检索
   - 数据筛选
   - 输出分流

4. **查看输出结果**：

   结果会保存在 ``data/output/`` 目录

命令行使用
----------

.. code-block:: bash

   # 直接执行任务
   ikos run "傅里叶变换的数学原理"

   # 指定输出格式
   ikos run "量子力学基础" --format markdown --format json

   # 指定输出目录
   ikos run "机器学习" --output ./my_results

配置示例
--------

编辑 ``config/settings.yaml`` 自定义配置：

.. code-block:: yaml

   model:
     default: "qwen3.5:7b"

   search:
     default_engine: "auto"
     max_results: 10

   output:
     default_formats:
       - "json"
       - "markdown"

使用本地模型
-----------

1. 确保 Ollama 正在运行：

   .. code-block:: bash

      ollama serve

2. 下载所需模型：

   .. code-block:: bash

      ollama pull qwen3.5:7b

3. 在配置文件中设置默认模型：

   .. code-block:: yaml

      model:
        default: "qwen3.5:7b"

下一步
------

- 阅读 :doc:`configuration` 了解详细配置选项
- 查看 :doc:`../dev/architecture` 了解系统架构
- 访问 :doc:`../api/core` 查看 API 文档
