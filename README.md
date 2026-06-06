<div align="center">

# 🚀 Model Deploy

### 大模型一键部署平台

[![平台](https://img.shields.io/badge/平台-3-blue?style=flat-square)]()
[![量化](https://img.shields.io/badge/量化-3-green?style=flat-square)]()
[![框架](https://img.shields.io/badge/框架-vLLM+TGI-orange?style=flat-square)]()
[![更新](https://img.shields.io/badge/更新-2025.06-red?style=flat-square)]()

*vLLM / TGI / Ollama · GGUF/GPTQ/AWQ 量化 · GPU 监控 · 一键部署*

</div>

---

# 本地模型部署与推理优化

一个完整的本地大模型部署方案，支持模型量化、推理加速、API 兼容、负载均衡。

## ✨ 特性

- 🚀 **高性能推理**: 集成 vLLM，支持 PagedAttention、连续批处理
- 📦 **模型量化**: 支持 GPTQ/AWQ/GGUF 量化，显著减少显存占用
- 🔌 **OpenAI 兼容 API**: 完全兼容 OpenAI Chat Completions API
- 🌊 **流式输出**: 支持 SSE 流式返回，实时生成响应
- 🔄 **多模型管理**: 动态加载/卸载模型，支持多模型切换
- 📊 **显存监控**: 实时监控 GPU 显存使用情况
- ⚖️ **负载均衡**: 多 Worker 调度，支持高并发请求
- 🛡️ **生产就绪**: 完整的错误处理、日志记录、健康检查

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端 (Client)                          │
│                    OpenAI SDK / HTTP 请求                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 应用层 (api.py)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat API     │  │ Completions  │  │ 模型管理 API          │  │
│  │ /v1/chat/... │  │ /v1/comp...  │  │ /v1/models/...       │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           │                                     │
│                           ▼                                     │
│              ┌────────────────────────┐                        │
│              │   模型管理器           │                        │
│              │   (model_manager.py)   │                        │
│              └───────────┬────────────┘                        │
└──────────────────────────┼──────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  模型 A      │  │  模型 B      │  │  模型 C      │
│  Engine      │  │  Engine      │  │  Engine      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────┐
│              推理引擎 (inference_engine.py)          │
│  ┌─────────────────┐      ┌─────────────────────┐  │
│  │ MockEngine      │      │ vLLMEngine          │  │
│  │ (测试/演示)     │      │ (生产环境)          │  │
│  └─────────────────┘      └─────────────────────┘  │
└─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                 量化模块 (quantizer.py)              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  GPTQ   │  │   AWQ   │  │  GGUF   │            │
│  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- CUDA 11.8+ (使用 GPU 推理时)
- 16GB+ GPU 显存 (加载 7B 模型时)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd model_deploy

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# GPU 环境额外安装 vLLM
pip install vllm
```

### 启动服务

```bash
# 使用默认配置启动（模拟模式，无需 GPU）
python api.py

# 指定端口和配置
python api.py --port 8080 --config config.yaml

# 生产环境启动（使用 Gunicorn）
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 聊天补全
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-7b-chat",
    "messages": [
      {"role": "system", "content": "你是一个有用的助手"},
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'

# 流式输出
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-7b-chat",
    "messages": [
      {"role": "user", "content": "写一首关于春天的诗"}
    ],
    "stream": true
  }'
```

### 使用 Python 客户端

```python
from openai import OpenAI

# 创建客户端
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # 本地服务不需要 API key
)

# 非流式调用
response = client.chat.completions.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "什么是大语言模型？"}
    ],
    temperature=0.7,
    max_tokens=200
)
print(response.choices[0].message.content)

# 流式调用
stream = client.chat.completions.create(
    model="qwen-7b-chat",
    messages=[
        {"role": "user", "content": "讲一个故事"}
    ],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 📚 API 文档

### Chat Completions

**POST** `/v1/chat/completions`

创建聊天补全，与 OpenAI API 完全兼容。

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| model | string | 是 | - | 模型名称 |
| messages | array | 是 | - | 消息列表 |
| temperature | float | 否 | 0.7 | 采样温度 (0-2) |
| top_p | float | 否 | 1.0 | 核采样概率 |
| n | integer | 否 | 1 | 生成选项数量 |
| stream | boolean | 否 | false | 是否流式输出 |
| stop | string/array | 否 | null | 停止词 |
| max_tokens | integer | 否 | null | 最大生成 token 数 |
| presence_penalty | float | 否 | 0.0 | 存在惩罚 (-2 到 2) |
| frequency_penalty | float | 否 | 0.0 | 频率惩罚 (-2 到 2) |

**响应示例:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen-7b-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是 AI 助手..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  }
}
```

### Completions

**POST** `/v1/completions`

创建文本补全。

### Models

**GET** `/v1/models`

列出所有可用模型。

**POST** `/v1/models/load`

加载模型。

**POST** `/v1/models/{model_name}/unload`

卸载模型。

### System

**GET** `/health`

健康检查。

**GET** `/v1/system/status`

获取系统状态（显存使用、请求数等）。

## ⚙️ 配置说明

配置文件 `config.yaml` 包含以下主要部分:

### 服务器配置

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1
```

### 模型配置

```yaml
models:
  - name: "qwen-7b-chat"
    path: "Qwen/Qwen-7B-Chat"
    format: "pytorch"
    quantization: "none"
    max_model_len: 8192
    auto_load: false
```

### 引擎配置

```yaml
engine:
  use_mock: true  # 无 GPU 时使用模拟引擎
  default_engine: "mock"
```

### 量化配置

```yaml
quantization:
  default_method: "gptq"
  gptq:
    bits: 4
    group_size: 128
```

## 🛠️ 技术栈

- **Web 框架**: FastAPI + uvicorn
- **数据验证**: Pydantic
- **异步 HTTP**: httpx
- **配置管理**: PyYAML
- **推理引擎**: vLLM (可选)
- **量化工具**: AutoGPTQ, AutoAWQ, llama.cpp
- **CLI 工具**: Rich

## 📁 项目结构

```
model_deploy/
├── api.py              # FastAPI 服务，OpenAI 兼容 API
├── models.py           # 数据模型定义
├── inference_engine.py # 推理引擎（Mock/vLLM）
├── model_manager.py    # 模型管理（加载/卸载/监控）
├── quantizer.py        # 模型量化模块
├── config.yaml         # 配置文件
├── requirements.txt    # Python 依赖
├── README.md           # 项目文档
└── .gitignore          # Git 忽略文件
```

## 🔧 高级用法

### 动态加载模型

```python
import requests

# 加载新模型
response = requests.post("http://localhost:8000/v1/models/load", json={
    "model_name": "my-model",
    "model_path": "/path/to/model",
    "model_format": "pytorch",
    "quantization": "none",
    "max_model_len": 4096,
})
```

### 模型量化

```python
from quantizer import quantize_model

# GPTQ 量化
quantized_path = quantize_model(
    model_path="Qwen/Qwen-7B-Chat",
    method="gptq",
    bits=4,
)

# AWQ 量化
quantized_path = quantize_model(
    model_path="Qwen/Qwen-7B-Chat",
    method="awq",
    bits=4,
)
```

### 监控系统状态

```python
import requests

# 获取系统状态
status = requests.get("http://localhost:8000/v1/system/status").json()
print(f"已加载模型: {status['models_loaded']}")
print(f"GPU 显存使用: {status['gpu_memory_used']}/{status['gpu_memory_total']} GB")
print(f"活跃请求数: {status['active_requests']}")
```

## 🐳 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行:

```bash
docker build -t model-deploy .
docker run -p 8000:8000 --gpus all model-deploy
```

## 📝 注意事项

1. **模拟模式**: 当前服务器没有 GPU，推理部分使用模拟模式，返回模拟响应
2. **GPU 要求**: 使用 vLLM 推理需要 NVIDIA GPU，建议 16GB+ 显存
3. **模型下载**: 首次使用需要从 HuggingFace 下载模型，请确保网络通畅
4. **显存管理**: 加载多个模型时注意显存使用，避免 OOM

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
