# Git 提交指南

## 应该提交的文件

### ✅ 必须提交

- `src/` - 所有源代码
- `config/` - 配置文件（不含敏感信息）
- `tests/` - 测试代码
- `docs/` - 文档
- `pyproject.toml` - 项目配置
- `.gitignore` - Git 忽略规则
- `README.md` - 项目说明
- `.github/workflows/` - CI/CD 配置（如果有）

### ❌ 不应提交

- `.venv/` - 虚拟环境
- `__pycache__/` - Python 缓存
- `data/` - 数据文件（已配置在 .gitignore）
- `*.pyc` - 编译文件
- `build/`, `dist/` - 构建产物
- `.pytest_cache/` - 测试缓存
- `htmlcov/` - 测试覆盖率报告
- `docs/_build/` - 构建的文档
- `uv.lock` - UV 锁定文件（可选）

## 快速开始

```bash
# 添加所有应该提交的文件
git add .

# 提交
git commit -m "feat: 完成 Phase 0 和 Phase 1"
```

## 提交信息格式

遵循 Conventional Commits：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式化
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 示例

```bash
git commit -m "feat: 实现 ModelProvider 和 SearchProvider 抽象接口"
git commit -m "fix: 修复导入错误"
git commit -m "docs: 更新 README"
```

## 代码质量检查（可选）

在提交前，可以手动运行检查工具：

```bash
# 格式化代码
black src/ tests/

# 检查代码
ruff check src/ tests/

# 类型检查
pyright src/

# 运行测试
pytest
```

## CI/CD

项目使用 GitHub Actions 进行自动化检查（待配置）：

- 代码格式化检查（Black）
- 代码质量检查（Ruff）
- 类型检查（Pyright）
- 单元测试（Pytest）
