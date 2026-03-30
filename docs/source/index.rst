Ikos 智能知识构建系统文档
==========================

欢迎来到 **Ikos** 的文档站点！

Ikos 是一个可控输出的智能知识构建系统，从网络实时检索信息，通过多轮 AI 处理与多模型投票决策，最终输出结构化的知识产物。

核心特性
--------

- **不依赖模型记忆**：使用三方信息求证，避免模型幻觉
- **多模型投票决策**：避免单一模型偏见，多视角覆盖
- **质量优先**：不追求速度，追求任务质量精良
- **输出必须重写**：原始数据必须经过模型系统性重写
- **知识图谱核心**：知识图谱贯穿全流程
- **用户可配置**：灵活配置输出形式

四阶段流程
----------

1. **需求解析** - 多轮转换 + 旁系监督 + 网络验证
2. **智能检索** - 多模型拆分搜索 + 备忘录迭代评审
3. **数据筛选** - 分合策略 + 多模型投票 + 知识图谱构建
4. **输出分流** - 用户配置 + 模板输出

文档目录
--------

.. toctree::
   :maxdepth: 2
   :caption: 用户指南

   user/installation
   user/quickstart
   user/configuration

.. toctree::
   :maxdepth: 2
   :caption: 开发指南

   dev/architecture
   dev/contributing

.. toctree::
   :maxdepth: 2
   :caption: API 文档

   api/core
   api/stage1
   api/stage2
   api/stage3
   api/stage4

快速开始
--------

安装依赖：

.. code-block:: bash

   uv pip install -e ".[dev]"

运行主程序：

.. code-block:: bash

   ikos

索引和表格
----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
