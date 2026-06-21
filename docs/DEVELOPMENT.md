# 开发指南

> 本文档为 `model_deploy` 项目的开发者提供环境搭建、代码规范、测试和贡献指南。

---

## 一、环境搭建

### 1.1 系统要求

| 依赖 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.10+ | 推荐 3.12 |
| pip | 23.0+ | 用于安装依赖 |
| Git | 2.30+ | 版本管理 |
| CUDA（可选） | 11.8+ | GPU 推理需要 |

### 1.2 快速搭建

```bash
# 克隆项目
git clone https://github.com/dirjaker/model_deploy.git
cd model_deploy
git checkout dev

# 创建虚拟环境（推荐 conda）
conda create -n model_deploy python=3.12 -y
conda activate model_deploy

# 安装核心依赖
pip install -r requirements.txt

# 安装 GPU 相关依赖（可选，需要 CUDA 环境）
# pip install vllm torch transformers accelerate
# pip install auto-gptq autoawq llama-cpp-python
```

### 1.3 依赖说明

**核心依赖（必须安装）：**
- `fastapi` + `uvicorn` — Web 框架与 ASGI 服务器
- `pydantic` — 数据模型验证
- `httpx` — 异步 HTTP 客户端
- `pyyaml` — 配置文件解析
- `rich` / `typer` — CLI 工具
- `psutil` — 系统监控
- `prometheus-client` — 指标采集

**可选依赖（GPU 环境）：**
- `vllm` — 高性能推理引擎
- `torch` + `transformers` — PyTorch 模型加载
- `auto-gptq` — GPTQ 量化
- `autoawq` — AWQ 量化
- `llama-cpp-python` — GGUF 推理

---

## 二、项目结构

```
model_deploy/
├── api.py                  # FastAPI 主服务入口
├── models.py               # Pydantic 数据模型
├── model_manager.py        # 模型生命周期管理
├── inference_engine.py     # 推理引擎抽象与实现
├── quantizer.py            # 量化模块
├── config.yaml             # 全局配置
├── requirements.txt        # Python 依赖
├── REVIEW.md               # 代码审查报告
│
├── src/
│   ├── __init__.py
│   ├── web/
│   │   ├── __init__.py
│   │   ├── app.py          # Web Dashboard
│   │   └── static/
│   │       └── index.html  # Dashboard 前端
│   └── macos/
│       ├── __init__.py
│       └── app.py          # macOS GUI
│
├── packaging/
│   └── py2app_setup.py     # macOS 打包脚本
│
├── docs/
│   ├── 技术文档.md          # 技术设计文档
│   ├── DEVELOPMENT.md      # 本文件
│   └── CHANGELOG.md        # 变更日志
│
└── assets/
    └── banner.svg          # 项目 Banner
```

---

## 三、运行方式

### 3.1 启动 API 服务

```bash
# 默认启动（Mock 引擎，端口 8000）
python api.py

# 自定义参数
python api.py --host 0.0.0.0 --port 8000 --config config.yaml --reload

# 使用真实 vLLM 引擎（需要 GPU）
# 修改 config.yaml 中 engine.use_mock 为 false
# 然后启动
python api.py
```

**命令行参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | 0.0.0.0 | 监听地址 |
| `--port` | 8000 | 监听端口 |
| `--config` | config.yaml | 配置文件路径 |
| `--workers` | 1 | Worker 数量 |
| `--reload` | False | 开发模式自动重载 |

### 3.2 启动 Web Dashboard

```bash
python -m src.web.app
# 访问 http://localhost:8080
```

### 3.3 启动 macOS GUI

```bash
python src/macos/app.py
```

### 3.4 打包 macOS 应用

```bash
python packaging/py2app_setup.py py2app
```

---

## 四、开发工作流

### 4.1 Git 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布版本 |
| `dev` | 开发分支（主要工作分支） |
| `feature/*` | 功能分支 |
| `fix/*` | 修复分支 |

### 4.2 提交规范

采用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Type 类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例：**
```
feat(quantizer): 添加 AWQ 量化支持
fix(api): 修复流式输出中途中断的问题
docs: 更新技术文档
```

---

## 五、代码规范

### 5.1 代码风格

项目使用以下工具保证代码质量：

| 工具 | 用途 | 命令 |
|------|------|------|
| **Black** | 代码格式化 | `black .` |
| **isort** | import 排序 | `isort .` |
| **flake8** | 代码检查 | `flake8 .` |
| **mypy** | 类型检查 | `mypy .` |

### 5.2 运行检查

```bash
# 格式化
black .
isort .

# 检查
flake8 .
mypy .

# 全部检查
black --check . && isort --check . && flake8 . && mypy .
```

### 5.3 编码规范

- 所有公共 API 使用类型注解
- 使用 Pydantic 模型定义数据结构
- 异步函数使用 `async def`
- 日志使用 `logging` 模块（不要用 `print`）
- 资源管理使用上下文管理器（`async with` / `with`）

---

## 六、测试

### 6.1 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=. --cov-report=html

# 运行特定测试文件
pytest tests/test_quantizer.py

# 运行异步测试
pytest --asyncio-mode=auto
```

### 6.2 测试结构

```
tests/
├── test_api.py              # API 端点测试
├── test_model_manager.py    # 模型管理器测试
├── test_inference_engine.py # 推理引擎测试
├── test_quantizer.py        # 量化模块测试
└── conftest.py              # 测试配置和 fixtures
```

### 6.3 Mock 模式测试

项目支持 **Mock 引擎模式**，无需 GPU 即可完整测试 API 功能：

```yaml
# config.yaml
engine:
  use_mock: true  # 使用 MockInferenceEngine
```

---

## 七、配置说明

### 7.1 修改配置

编辑 `config.yaml` 文件，主要配置项：

```yaml
# 引擎选择
engine:
  use_mock: true        # true=Mock引擎（测试用），false=vLLM引擎（GPU环境）
  default_engine: "mock"

# 预加载模型
models:
  - name: "my-model"
    path: "/path/to/model"   # 本地路径或 HuggingFace ID
    format: "pytorch"         # pytorch | gptq | awq | gguf
    quantization: "none"      # none | gptq | awq | gguf
    auto_load: true           # 启动时自动加载
```

### 7.2 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | 允许的跨域来源（逗号分隔） | `http://localhost,http://127.0.0.1` |

---

## 八、常见问题

### Q: 启动报错 "No module named 'vllm'"
A: vLLM 是可选依赖，仅在 GPU 环境下需要。确保 `config.yaml` 中 `engine.use_mock: true` 即可使用 Mock 引擎。

### Q: 如何添加新的推理引擎？
A: 继承 `BaseInferenceEngine`，实现所有抽象方法，然后在 `InferenceEngineFactory.create()` 中注册。

### Q: 如何添加新的量化方法？
A: 继承 `BaseQuantizer`，实现 `quantize()` 和 `validate()` 方法，然后在 `QuantizerFactory.create()` 中注册。

### Q: macOS 打包失败怎么办？
A: 确保安装了 `py2app`（`pip install py2app`），并且在 macOS 系统上运行。打包会排除 `numpy`、`torch` 等大型依赖。

---

## 九、相关文档

- [技术文档](技术文档.md) — 系统架构和核心模块设计
- [变更日志](CHANGELOG.md) — 版本变更记录
- [代码审查报告](../REVIEW.md) — 安全和质量审查
