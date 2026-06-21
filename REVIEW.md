# 代码审查报告 - model_deploy

**审查日期**: 2026-06-22
**审查范围**: 全部 Python 源文件（11 个）、配置文件、依赖文件

---

## 🔴 致命问题

### 1. CORS 配置过于宽松 + 允许凭据
- **文件**: `api.py` **行号**: 106-112
- **描述**: `allow_origins=["*"]` 配合 `allow_credentials=True`，任何来源都可以携带凭据（如 Cookie）发起跨域请求。这在 OWASP 中属于严重安全配置错误。
- **修复建议**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000"],  # 限制为前端域名
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["*"],
  )
  ```

### 2. API 无认证/鉴权机制
- **文件**: `api.py` **行号**: 全部路由
- **描述**: 所有 API 端点（包括模型加载/卸载等管理接口）均无任何认证。config.yaml 中 `security.api_key` 为空字符串，代码中也未实现 API Key 校验逻辑。任何能访问网络的人都可以加载/卸载模型、获取系统状态。
- **修复建议**: 实现中间件校验 `Authorization: Bearer <api_key>`，至少对管理类接口（`/v1/models/load`, `/v1/models/{name}/unload`）强制认证。

### 3. 异常详情泄露到客户端
- **文件**: `api.py` **行号**: 119-126
- **描述**: 全局异常处理器将 `str(exc)` 直接返回给客户端（`details={"message": str(exc)}`），可能泄露内部路径、栈信息等敏感数据。
- **修复建议**:
  ```python
  # 生产环境只返回通用错误信息，详细错误仅记录到日志
  content=ErrorResponse(error="内部服务器错误", code=500, details={"message": "请联系管理员"})
  ```

### 4. 监听 0.0.0.0 无 IP 限制
- **文件**: `api.py` **行号**: 304; `config.yaml` **行号**: 5
- **描述**: 默认绑定 `0.0.0.0` 且 `security.allowed_ips` 为空，服务暴露在所有网络接口。config 中有 `allowed_ips` 和 `rate_limit` 配置项但代码中**完全没有实现**。
- **修复建议**: 实现 IP 白名单中间件和速率限制中间件，或使用反向代理（Nginx）限制访问。

---

## 🟡 警告问题

### 5. CORS 同样出现在 Web Dashboard
- **文件**: `src/web/app.py` **行号**: 47-52
- **描述**: Web Dashboard 同样使用 `allow_origins=["*"]`，虽无 `allow_credentials`，但仍过于宽松。
- **修复建议**: 限制为本地开发地址或配置文件指定的域名。

### 6. 模型路径未做安全校验（路径穿越风险）
- **文件**: `api.py` **行号**: 224-234（load_model）
- **描述**: `ModelConfig.model_path` 直接来自用户输入，未校验是否在允许目录内。攻击者可指定任意路径加载模型，可能读取服务器上的敏感文件。
- **修复建议**: 对 `model_path` 做白名单校验，限制只能加载指定目录下的模型。

### 7. 端口输入未校验
- **文件**: `src/macos/app.py` **行号**: 96
- **描述**: `int(self.port_var.get())` 未做异常捕获和范围校验，用户输入非法字符会导致崩溃。
- **修复建议**:
  ```python
  try:
      port = int(self.port_var.get())
      if not (1024 <= port <= 65535):
          raise ValueError
  except ValueError:
      messagebox.showerror("错误", "端口必须是 1024-65535 之间的整数")
      return
  ```

### 8. 文件操作未使用上下文管理器
- **文件**: `quantizer.py` **行号**: 132, 144, 204, 216, 260, 265, 279
- **描述**: 部分 `open()` 调用未使用 `with` 语句，可能导致文件句柄泄漏。
- **修复建议**: 统一使用 `with open(...) as f:` 模式。

### 9. 全局可变状态
- **文件**: `api.py` **行号**: 50-52
- **描述**: `model_manager` 和 `config` 为全局变量，在多 worker 模式下可能导致状态不一致。
- **修复建议**: 使用 FastAPI 的依赖注入系统管理共享状态。

### 10. 依赖版本未完全锁定
- **文件**: `requirements.txt` **行号**: 全文
- **描述**: 部分依赖使用精确版本（`fastapi==0.109.0`），但 `py2app>=0.28.0` 使用范围约束，可能引入不兼容版本。
- **修复建议**: 使用 `pip freeze` 生成完整锁定文件，或使用 `poetry.lock`/`uv.lock`。

---

## 🔵 建议

### 11. GPU 显存监控为模拟数据
- **文件**: `model_manager.py` **行号**: 49-60
- **描述**: `get_memory_info()` 返回硬编码的模拟值，实际代码被注释。生产环境会错误地允许加载超出显存的模型。
- **修复建议**: 添加运行时检测，当无 GPU 时返回明确标识而非模拟数据。

### 12. 缺少请求体大小限制
- **文件**: `api.py`
- **描述**: 未对请求体大小做限制，大 payload 可能导致内存溢出。
- **修复建议**: 配置 Uvicorn 的 `--limit-max-request-size` 或使用 Nginx 限制。

### 13. 缺少健康检查详细信息
- **文件**: `api.py` **行号**: 265-268
- **描述**: `/health` 端点仅返回 `"healthy"`，未检查模型加载状态、GPU 可用性等。
- **修复建议**: 实现深度健康检查，验证关键依赖是否就绪。

### 14. 日志级别硬编码
- **文件**: `api.py` **行号**: 32-35
- **描述**: `logging.basicConfig(level=logging.INFO)` 硬编码，无法通过配置调整。
- **修复建议**: 从 config.yaml 读取日志级别。

---

## 总结评分

| 维度 | 分数 | 说明 |
|------|------|------|
| **安全** | 4/10 | CORS 全开、无认证、异常泄露、路径未校验，多项致命问题 |
| **质量** | 6/10 | 代码结构清晰，但全局状态管理、文件操作、输入校验有瑕疵 |
| **架构** | 7/10 | 工厂模式、异步生命周期管理、Pydantic 模型设计良好 |

**总体评价**: 项目架构设计合理，但安全防护严重不足。在部署到生产环境前，必须解决认证、CORS、异常泄露等问题。
