<div align="center">

<img src="assets/banner.svg" width="100%" alt="本地模型部署工具">

<br>

### 🚀 本地模型部署工具

[![Stars](https://img.shields.io/github/stars/dirjaker/model_deploy?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/model_deploy/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/model_deploy?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/model_deploy/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/model_deploy?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/model_deploy/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/model_deploy?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/model_deploy/blob/dev/LICENSE)

</div>

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 📦 **模型量化** | 支持 GPTQ、AWQ、GGUF 三种量化格式，大幅降低显存占用 |
| ⚡ **vLLM 推理** | 集成 vLLM 高性能推理引擎，支持 PagedAttention 与连续批处理 |
| 🔌 **OpenAI 兼容 API** | 提供 `/v1/chat/completions` 和 `/v1/completions` 等标准接口 |
| 🖥️ **Web 管理面板** | 基于 FastAPI 的 Web Dashboard，可视化管理模型与监控状态 |
| 📊 **系统监控** | GPU 显存使用、推理延迟、请求量等实时指标采集 |
| 🔧 **多模型管理** | 支持多模型加载/卸载切换、空闲自动清理、显存预估 |
| 🖥️ **macOS 桌面应用** | 基于 tkinter 的 GUI 客户端，一键启停 Web 服务 |
| 🛡️ **CORS 安全配置** | 通过环境变量限制跨域访问来源 |


## 📁 项目结构

```
model_deploy/
├── api.py                  # FastAPI 主服务（OpenAI 兼容 API）
├── models.py               # Pydantic 数据模型定义
├── model_manager.py        # 模型生命周期管理（加载/卸载/切换/清理）
├── inference_engine.py     # 推理引擎抽象与实现（Mock / vLLM）
├── quantizer.py            # 模型量化模块（GPTQ / AWQ / GGUF）
├── config.yaml             # 全局配置文件
├── requirements.txt        # Python 依赖
├── REVIEW.md               # 代码审查报告
├── src/
│   ├── web/
│   │   ├── app.py          # Web Dashboard 后端
│   │   └── static/
│   │       └── index.html  # Web Dashboard 前端
│   └── macos/
│       └── app.py          # macOS GUI 客户端
├── packaging/
│   └── py2app_setup.py     # macOS 打包脚本
├── docs/
│   ├── 技术文档.md          # 技术设计文档
│   ├── DEVELOPMENT.md      # 开发指南
│   └── CHANGELOG.md        # 变更日志
└── assets/
    └── banner.svg          # 项目 Banner
```


## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/dirjaker/model_deploy.git
cd model_deploy

# 创建虚拟环境
conda create -n model_deploy python=3.12 -y
conda activate model_deploy

# 安装依赖
pip install -r requirements.txt

# 启动 API 服务（默认端口 8000）
python api.py

# 启动 Web Dashboard（默认端口 8080）
python -m src.web.app
```

### API 使用示例

```bash
# 聊天补全（OpenAI 兼容）
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-7b-chat",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'

# 列出可用模型
curl http://localhost:8000/v1/models

# 加载模型
curl -X POST http://localhost:8000/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "qwen-7b-chat",
    "model_path": "Qwen/Qwen-7B-Chat",
    "model_format": "pytorch"
  }'

# 系统状态
curl http://localhost:8000/v1/system/status
```


## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **推理引擎** | vLLM（PagedAttention + 连续批处理） |
| **量化** | AutoGPTQ / AutoAWQ / llama.cpp（GGUF） |
| **API 框架** | FastAPI + Uvicorn |
| **数据模型** | Pydantic v2 |
| **监控** | Prometheus Client / psutil |
| **GUI** | tkinter（macOS 桌面应用） |
| **打包** | py2app（macOS .app） |
| **开发工具** | Black / isort / flake8 / mypy / pytest |


## 📝 开发日志

- [x] 模型量化模块（GPTQ / AWQ / GGUF）
- [x] Mock 推理引擎（无 GPU 环境测试）
- [x] vLLM 推理引擎骨架
- [x] OpenAI 兼容 API（chat/completions）
- [x] 流式输出支持
- [x] 多模型加载/卸载/切换
- [x] GPU 显存监控与空闲模型清理
- [x] Web 管理面板
- [x] macOS 桌面 GUI
- [x] 代码审查报告
- [ ] vLLM 引擎完整实现（GPU 环境）
- [ ] 负载均衡与多 Worker 集群
- [ ] API 认证与限流中间件
- [ ] 语义缓存（Redis + 向量检索）


## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/model_deploy](https://github.com/dirjaker/model_deploy)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
