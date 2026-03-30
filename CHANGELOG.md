# 更新日志 (Changelog)

本文档记录 Ikos 项目的所有重要更新。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.1.0] - 2026-03-31

### 新增 ✨

#### 核心功能
- **第一阶段：需求解析机制**
  - 实现需求解析器 (`RequirementParser`)
  - 实现网络验证器 (`NetworkValidator`)
  - 实现旁系监督器 (`SideSupervisor`)
  - 支持多轮解析和球形知识空间构建

- **第二阶段：智能检索机制**
  - 实现任务拆分器 (`TaskSplitter`)
  - 实现搜索执行器 (`SearchExecutor`)
  - 实现备忘录管理器 (`MemoManager`)
  - 支持多模型拆分和备忘录迭代评审

- **第三阶段：数据筛选机制**
  - 实现初筛过滤器 (`InitialFilter`)
  - 实现数据合并器 (`DataMerger`)
  - 实现知识图谱构建器 (`KnowledgeGraphBuilder`)
  - 实现数据精筛与重写器 (`DataRefiner`)
  - 支持分合策略和多模型投票

- **第四阶段：输出分流机制**
  - 实现输出分流器 (`OutputDispatcher`)
  - 实现文件输出器 (`FileOutputter`)
  - 实现数据库输出器 (`DatabaseOutputter`)
  - 支持 JSON、Markdown 等多种输出格式

#### 核心抽象层
- **模型提供者接口**
  - `ModelProvider` 抽象基类
  - `OllamaProvider` 实现（支持 Ollama 本地模型）
  - `OpenAICompatibleProvider` 实现（支持 OpenAI 兼容 API）
  - 多模型批量调用和投票决策机制

- **搜索提供者接口**
  - `SearchProvider` 抽象基类
  - `PlaywrightSearchProvider` 实现（基于浏览器自动化）
  - 支持多搜索引擎（Google、Bing、百度、DuckDuckGo）
  - 网页内容抓取和正文提取

- **投票引擎**
  - `VoteEngine` 实现
  - 支持多数投票和加权投票策略
  - 一致性计算和结果接受判断

#### 端到端流程
- **最小竖直流管道**
  - `IkosPipeline` 编排器
  - 完整的四阶段流程实现
  - 命令行入口工具

#### 工具与配置
- **配置文件**
  - `config/settings.yaml` - 主配置文件
  - `config/models.yaml` - 多模型配置
  - `config/prompts/*.yaml` - 四阶段提示词模板

- **工具函数**
  - 配置加载器 (`load_config`, `load_yaml`)
  - 日志配置 (`setup_logger`)
  - 基于 `loguru` 的日志系统

#### 测试
- **单元测试**
  - 核心组件测试 (`test_pipeline.py`)
  - 覆盖所有主要模块

- **集成测试**
  - 端到端流程测试 (`test_integration.py`)
  - 配置和模板加载测试

### 技术栈 🛠️

- **Python 3.13+**
- **模型推理**: Ollama, OpenAI 兼容 API
- **浏览器自动化**: Playwright
- **向量数据库**: Chroma, Milvus（配置支持）
- **图数据库**: Neo4j（配置支持）
- **配置管理**: PyYAML, Pydantic
- **日志**: loguru
- **测试**: pytest, pytest-cov

### 项目结构 📁

```
Ikos/
├── ikos/                      # 主包
│   ├── core/                  # 核心抽象层
│   │   ├── model_provider.py
│   │   ├── search_provider.py
│   │   ├── vote_engine.py
│   │   ├── types.py
│   │   └── pipeline.py        # 端到端管道
│   ├── stage1_requirement/    # 第一阶段
│   ├── stage2_search/         # 第二阶段
│   ├── stage3_filter/         # 第三阶段
│   ├── stage4_output/         # 第四阶段
│   ├── utils/                 # 工具函数
│   └── main.py                # 入口
├── config/                    # 配置文件
│   ├── settings.yaml
│   ├── models.yaml
│   └── prompts/
├── tests/                     # 测试
└── data/                      # 数据目录（输出）
```

### 已知限制 ⚠️

- **0.1.0 版本为最小可用版本**，部分功能为简化实现：
  - 多模型投票机制使用简化逻辑
  - 数据库输出为模拟实现（未实际连接）
  - 网络验证使用基础关键词匹配
  - 备忘录评审使用单模型而非多模型

- **需要外部服务**：
  - Ollama 服务（用于模型推理）
  - Playwright 浏览器（用于搜索）

### 下一步计划 📋

- **0.2.0 版本**
  - 完善多模型投票机制
  - 实现真实的数据库连接
  - 优化网络验证算法
  - 改进备忘录评审流程

- **0.3.0 版本**
  - 添加可观测性和配置驱动
  - 完善日志和监控
  - 提高测试覆盖率

---

## 版本说明

### 语义化版本规则

- **MAJOR.MINOR.PATCH** (主版本。次版本。修订号)
- **0.x.y** 表示产品形态仍在收敛，允许较频繁调整
- **1.0.0** 起将明确官方最小路径与兼容性承诺

### 版本号含义

| 段位 | 含义 | 典型变更 |
|------|------|----------|
| **MAJOR** | 破坏性变更 | 配置结构不兼容、CLI 行为大变等 |
| **MINOR** | 向后兼容的功能增量 | 新能力、新模块、新输出格式 |
| **PATCH** | 向后兼容的修正 | 缺陷修复、安全更新、文档勘误 |

---

## 链接

- [项目仓库](https://github.com/jamsyan/Ikos)
- [架构文档](docs/智能知识构建系统架构文档.md)
- [问题反馈](https://github.com/jamsyan/Ikos/issues)

[0.1.0]: https://github.com/jamsyan/Ikos/releases/tag/v0.1.0
