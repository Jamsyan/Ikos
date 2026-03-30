贡献指南
========

欢迎参与 Ikos 项目的开发！

开发环境设置
------------

1. **克隆仓库**：

   .. code-block:: bash

      git clone https://github.com/jamsyan/Ikos.git
      cd Ikos

2. **安装开发依赖**：

   .. code-block:: bash

      uv pip install -e ".[dev]"

3. **安装 pre-commit 钩子**：

   .. code-block:: bash

      pre-commit install

4. **安装 Playwright 浏览器**：

   .. code-block:: bash

      playwright install

开发流程
--------

1. **创建分支**：

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **编写代码**：

   - 遵循 PEP 8 风格指南
   - 添加类型注解
   - 编写单元测试

3. **运行检查**：

   .. code-block:: bash

      # 代码格式化
      black src/ tests/

      # 代码检查
      ruff check src/ tests/

      # 类型检查
      pyright src/

      # 运行测试
      pytest

4. **提交更改**：

   pre-commit 会自动运行检查，通过后才能提交。

   .. code-block:: bash

      git add .
      git commit -m "feat: 添加新功能"

5. **推送并创建 PR**：

   .. code-block:: bash

      git push origin feature/your-feature-name

代码规范
--------

**格式化**：使用 Black，行宽 100

**导入排序**：使用 Ruff (isort)

**类型检查**：使用 Pyright (strict 模式)

**代码质量**：使用 Pylint

**文档字符串**：使用 Google 风格

提交信息规范
------------

遵循 Conventional Commits：

- ``feat:`` 新功能
- ``fix:`` Bug 修复
- ``docs:`` 文档更新
- ``style:`` 代码格式化
- ``refactor:`` 重构
- ``test:`` 测试相关
- ``chore:`` 构建/工具相关

测试要求
--------

- 新功能必须包含单元测试
- 测试覆盖率不低于 80%
- 所有现有测试必须通过

文档要求
--------

- 公共 API 必须有文档字符串
- 新功能需要更新用户文档
- 重大变更需要更新架构文档

问题反馈
--------

请使用 GitHub Issues 反馈问题或提出建议。

感谢贡献！
