# 原生推理引擎快速开始

## 🎯 本次更新内容

实现了完整的**原生推理引擎核心**，基于 Transformers + PyTorch，不依赖 Ollama 等外部推理引擎。

### 核心功能

- ✅ 硬件自动检测（GPU/CPU/内存）
- ✅ 显存精细化管理（VRAM 池化）
- ✅ 多量化等级支持（NF4/INT8/FP16/FP32）
- ✅ CPU-GPU 混合推理（4GB 显存可运行 7B 模型）
- ✅ 智能引擎切换（自动/手动）
- ✅ 完整的 ModelProvider 接口

## 📦 安装步骤

### 1. 切换到新分支

```bash
git checkout feature/native-inference-engine
```

### 2. 安装依赖

```bash
# 使用 uv 安装所有依赖
uv sync
```

### 3. 安装浏览器（用于搜索功能）

```bash
playwright install
```

### 4. 验证安装

```bash
# 测试硬件检测
python -c "from ikos.core import detect_hardware; print(detect_hardware())"
```

## 🚀 快速使用

### 基础示例

```python
from ikos.core import create_native_engine

# 创建引擎（自动检测硬件）
engine = create_native_engine(quantization="auto")

# 调用模型
response = engine.call(
    prompt="请介绍一下傅里叶变换",
    model="Qwen/Qwen2.5-7B-Instruct",
    max_tokens=1024
)

print(response.content)
```

### 手动指定量化

```python
# 根据硬件选择量化等级
# 4GB 显存 -> NF4
# 8GB 显存 -> INT8
# 16GB 显存 -> FP16
engine = create_native_engine(quantization="NF4")
```

### 多模型投票

```python
result = engine.vote(
    prompt="解释量子力学",
    models=[
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-3B-Instruct",
    ],
    voting_strategy="majority"
)

print(f"获胜模型：{result.winner_model}")
print(f"答案：{result.winner_content}")
```

## 📊 硬件分级与推荐

| 场景     | 显存   | 推荐量化 | 可运行模型       |
|----------|--------|----------|------------------|
| 极限场景  | 4GB    | NF4      | 7B (CPU-GPU 混合) |
| 基础场景  | 8GB    | INT8     | 7B (GPU)         |
| 性能场景  | 16GB   | FP16     | 14B (GPU)        |
| 旗舰场景  | 24GB+  | FP32     | 35B+ (GPU)       |

## 📁 新增文件

### 核心模块

```
ikos/core/
├── hardware_detector.py        # 硬件检测
├── vram_manager.py             # 显存管理
├── quantization_config.py      # 量化配置
├── native_model_loader.py      # 模型加载
├── native_inference_engine.py  # 推理引擎
├── engine_switcher.py          # 引擎切换
└── __init__.py                 # 导出（已更新）
```

### 测试文件

```
tests/
├── test_hardware.py            # 硬件检测测试
├── test_vram_manager.py        # 显存管理测试
├── test_quantization.py        # 量化配置测试
└── test_native_engine.py       # 引擎集成测试
```

### 配置文件

```
config/
├── settings.yaml               # 新增 native_engine 配置
└── models.yaml                 # 新增 native_models 配置
```

### 文档

```
docs/
├── 原生推理引擎使用指南.md      # 完整使用文档
└── 原生引擎实现总结.md          # 实现总结
```

## ⚙️ 配置说明

### settings.yaml

```yaml
native_engine:
  enabled: true
  quantization: "auto"  # NF4/INT4/INT8/FP16/FP32/auto
  memory_reserve_ratio: 0.1
  cache_dir: "./data/models"
  engine_mode: "auto"  # auto/native/ollama/openai
```

### models.yaml

```yaml
native_models:
  main:
    name: "Qwen/Qwen2.5-7B-Instruct"
    quantization: "NF4"
  
  lightweight:
    name: "Qwen/Qwen2.5-3B-Instruct"
    quantization: "INT4"
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/test_hardware.py -v
pytest tests/test_vram_manager.py -v
pytest tests/test_quantization.py -v
pytest tests/test_native_engine.py -v
```

## 🔧 常见问题

### Q: bitsandbytes 安装失败

**A**: Windows 用户可以使用：
```bash
pip install bitsandbytes-windows
```

或降级使用 INT8 量化：
```python
engine = create_native_engine(quantization="INT8")
```

### Q: 显存不足 OOM

**A**: 
1. 降低量化等级（FP16 -> INT8 -> NF4）
2. 使用更小的模型（7B -> 3B）
3. CPU-GPU 混合推理会自动启用

### Q: 模型下载慢

**A**: 使用魔塔社区（已默认配置）：
```python
from ikos.core import NativeModelLoader
loader = NativeModelLoader()
loader.download_model("Qwen/Qwen2.5-7B-Instruct")
```

## 📚 详细文档

- [完整使用指南](docs/原生推理引擎使用指南.md)
- [实现总结](docs/原生引擎实现总结.md)
- [架构文档](docs/智能知识构建系统架构文档.md)

## 🎯 下一步

1. **测试验证** - 在不同硬件环境测试
2. **性能基准** - 建立性能指标
3. **业务集成** - 与四阶段 Pipeline 集成
4. **UI 开发** - 任务管理与进度展示

## 📝 技术栈

- **推理框架**: PyTorch + Transformers
- **量化库**: bitsandbytes (NF4/INT4/INT8)
- **硬件检测**: pynvml + psutil
- **模型源**: 魔塔社区 (优先) + HuggingFace

## ✨ 关键特性

### 1. 硬件自适应

自动检测 GPU、CPU、内存，智能推荐量化等级和引擎模式。

### 2. 显存池化管理

- 保留 10% 显存余量
- 优先级调度（P0 可抢占）
- 实时监控

### 3. CPU-GPU 混合推理

使用 `accelerate` 的 `device_map="auto"`，自动在 CPU 和 GPU 间分配模型层。

### 4. 多模型投票

完整的投票机制，支持多数投票和加权投票。

### 5. 引擎热切换

支持原生引擎、Ollama、OpenAI 兼容 API 之间切换。

---

**分支**: `feature/native-inference-engine`  
**版本**: v0.2.0  
**日期**: 2026-03-31
