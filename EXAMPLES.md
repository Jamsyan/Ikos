# Ikos 使用示例

本文档提供 Ikos 0.1.0 版本的使用示例。

## 前置要求

1. **Python 3.13+**
2. **Ollama 服务**（用于模型推理）
   ```bash
   # 安装 Ollama
   # Windows: 访问 https://ollama.ai/download
   # Linux/macOS: curl -fsSL https://ollama.ai/install.sh | sh
   
   # 拉取模型
   ollama pull qwen3.5:7b
   ```

3. **Playwright 浏览器**
   ```bash
   pip install playwright
   playwright install
   ```

4. **项目依赖**
   ```bash
   pip install -e .
   ```

## 基本用法

### 命令行使用

最简单的使用方式：

```bash
# 运行主程序
python main.py "我想知道傅里叶变换的数学知识"
```

### 自定义输出格式

```bash
# 输出 JSON 和 Markdown 格式
python main.py "量子力学基础概念" --output-format json,markdown

# 只输出 JSON
python main.py "机器学习入门" --output-format json
```

## 输出结果

执行成功后，输出文件将保存在 `data/output/` 目录：

```
data/output/
├── knowledge_graph.json      # 知识图谱
├── structured_data.json      # 结构化数据
└── output.md                 # Markdown 文档
```

### 知识图谱示例

```json
{
  "nodes": [
    {
      "id": "core",
      "label": "傅里叶变换",
      "type": "core_concept",
      "description": "核心主题：傅里叶变换"
    },
    {
      "id": "entity_0",
      "label": "傅里叶级数",
      "type": "concept",
      "description": "傅里叶级数是..."
    }
  ],
  "edges": [
    {
      "source": "core",
      "target": "entity_0",
      "relation": "related_to"
    }
  ]
}
```

## 编程使用

### 使用 Python API

```python
from ikos.core.pipeline import IkosPipeline

# 创建管道
pipeline = IkosPipeline("config/settings.yaml")

# 执行流程
result = pipeline.run(
    user_input="我想知道傅里叶变换的数学知识",
    output_config={
        "output_type": "file",
        "formats": ["json", "markdown"],
        "output_path": "./data/output"
    }
)

# 查看结果
if result["status"] == "success":
    print(f"输出文件数：{len(result['output_files'])}")
    for file in result["output_files"]:
        print(f"  - {file['filename']}: {file['path']}")
```

### 自定义配置

```python
from ikos.core import OllamaProvider, PlaywrightSearchProvider
from ikos.core.pipeline import IkosPipeline

# 自定义模型提供者
model_provider = OllamaProvider(
    base_url="http://localhost:11434",
    timeout=180  # 3 分钟超时
)

# 自定义搜索提供者
search_provider = PlaywrightSearchProvider(
    headless=False,  # 显示浏览器
    timeout=60000,   # 60 秒超时
    default_engine="bing"
)

# 使用自定义组件创建管道
pipeline = IkosPipeline()
pipeline.model_provider = model_provider
pipeline.search_provider = search_provider

# 执行
result = pipeline.run("你的问题")
```

## 配置说明

### 主配置 (config/settings.yaml)

```yaml
# 模型配置
model:
  default: "qwen3.5:7b"
  ollama:
    base_url: "http://localhost:11434"
    timeout: 120

# 搜索配置
search:
  default_engine: "auto"  # auto/google/bing/baidu/duckduckgo
  max_results: 10
  browser:
    headless: true
    timeout: 30000

# 输出配置
output:
  directory: "./data/output"
  default_formats:
    - "json"
    - "markdown"
```

### 多模型配置 (config/models.yaml)

```yaml
# 单模型模式（0.1.0 版本）
default_model: &default_model
  name: "qwen3.5:7b"
  provider: "ollama"
  temperature: 0.7
  max_tokens: 2048

# 多模型投票配置（0.2.0+ 版本使用）
multi_model_config:
  splitters:
    - name: "qwen3.5:7b"
      weight: 1.0
    - name: "qwen3.5:14b"
      weight: 1.2
  # ...
```

## 常见问题

### Q: Ollama 服务未运行

**错误信息**: `Connection refused` 或 `Ollama 服务未运行`

**解决方法**:
```bash
# 启动 Ollama 服务
ollama serve

# 验证服务
curl http://localhost:11434/api/tags
```

### Q: Playwright 浏览器未安装

**错误信息**: `playwright 库未安装`

**解决方法**:
```bash
# 安装浏览器
playwright install
```

### Q: 模型调用超时

**解决方法**: 增加超时时间
```yaml
# config/settings.yaml
model:
  ollama:
    timeout: 180  # 增加到 3 分钟
```

### Q: 输出文件为空

**可能原因**:
1. 搜索结果为空 - 检查网络连接
2. 模型响应失败 - 检查 Ollama 服务
3. 内容不相关 - 调整输入问题

## 下一步

- 查看 [架构文档](docs/智能知识构建系统架构文档.md) 了解系统设计
- 查看 [CHANGELOG](CHANGELOG.md) 了解版本更新
- 查看 [README](README.md) 了解项目概述

## 获取帮助

- 📧 Email: jihanyang123@163.com
- 💬 Issues: [GitHub Issues](https://github.com/jamsyan/Ikos/issues)
