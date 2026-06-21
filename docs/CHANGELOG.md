# 变更日志

> 本文档记录 `model_deploy` 项目的所有重要变更。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [未发布] - dev 分支

### 计划中
- vLLM 引擎完整实现（GPU 环境推理）
- API Key 认证中间件
- IP 白名单与速率限制
- 语义缓存（Redis + 向量检索）
- 深度健康检查
- 请求体大小限制

---

## [1.2.0] - 2026-06-22

### 新增
- **Web Dashboard**: 基于 FastAPI 的管理面板 (`src/web/app.py`)
  - 模型列表、加载/卸载 API
  - 系统状态查询
  - 聊天测试接口
  - 前端静态页面 (`src/web/static/index.html`)
- **macOS 桌面客户端**: 基于 tkinter 的 GUI (`src/macos/app.py`)
  - 一键启停 Web 服务
  - 端口配置、模型列表、系统状态查询
  - 活动日志面板
  - 深色主题 UI
- **macOS 打包**: py2app 打包脚本 (`packaging/py2app_setup.py`)
- **代码审查报告**: `REVIEW.md` — 安全和质量审查

### 修复
- CORS 配置限制为本地访问（通过 `CORS_ORIGINS` 环境变量）

### 安全
- CORS 全局限制为 `http://localhost` 和 `http://127.0.0.1`

---

## [1.1.0] - 2026-06-22

### 新增
- **README 优化**: 统一科技风格 + SVG Banner + MIT License
- **代码审查**: 添加完整代码审查和安全扫描报告

### 修复
- Banner 比例调整为 4:6
- Banner 布局优化，副标题改为中文项目名
- Banner 文字溢出自适应字号
- 主标题左侧留白增加到 60px

---

## [1.0.0] - 2026-06-22

### 新增
- **核心框架**
  - `api.py` — FastAPI 主服务，OpenAI 兼容 API
  - `models.py` — Pydantic v2 数据模型（请求/响应/配置）
  - `model_manager.py` — 模型生命周期管理（加载/卸载/切换/清理）
  - `inference_engine.py` — 推理引擎抽象层（Mock + vLLM）
  - `quantizer.py` — 量化模块（GPTQ/AWQ/GGUF）
  - `config.yaml` — 全局配置文件

- **API 端点**
  - `POST /v1/chat/completions` — 聊天补全（支持流式输出）
  - `POST /v1/completions` — 文本补全（支持流式输出）
  - `GET /v1/models` — 列出可用模型
  - `POST /v1/models/load` — 加载模型
  - `POST /v1/models/{name}/unload` — 卸载模型
  - `GET /v1/models/{name}/info` — 模型详情
  - `GET /health` — 健康检查
  - `GET /v1/system/status` — 系统状态
  - `GET /v1/system/engines` — 可用引擎列表
  - `GET /v1/system/quantization-methods` — 量化方法列表

- **推理引擎**
  - `MockInferenceEngine` — 无 GPU 环境测试引擎
  - `VLLMInferenceEngine` — vLLM 高性能推理引擎骨架
  - `InferenceEngineFactory` — 引擎工厂，按配置自动选择

- **量化模块**
  - `GPTQQuantizer` — GPTQ 量化器（基于二阶信息）
  - `AWQQuantizer` — AWQ 量化器（激活值感知）
  - `GGUFQuantizer` — GGUF 量化器（llama.cpp 格式）
  - `QuantizerFactory` — 量化器工厂
  - `quantize_model()` — 便捷量化函数

- **模型管理**
  - 多模型加载/卸载/切换
  - GPU 显存监控（`GPUMemoryMonitor`）
  - 模型显存需求估算
  - 空闲模型自动清理
  - 异步锁保护并发安全
  - 系统状态统计

- **文档**
  - `README.md` — 项目介绍与快速开始
  - `docs/技术文档.md` — 技术设计文档
  - `requirements.txt` — Python 依赖清单

- **配置**
  - YAML 配置文件，支持服务、引擎、模型、量化、推理、GPU、日志、安全等配置
  - 预配置 5 个常用模型（Qwen、Llama-2、ChatGLM）

---

## 版本说明

- 版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范
- `MAJOR.MINOR.PATCH` 格式
- 未发布功能在 `dev` 分支开发
