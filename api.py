"""
FastAPI 服务模块
提供 OpenAI 兼容的 API 接口
"""
import asyncio
import os
import logging
import time
from typing import Optional
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models import (
    ChatCompletionRequest,
    CompletionRequest,
    ChatCompletionResponse,
    CompletionResponse,
    StreamResponse,
    ModelConfig,
    ModelInfo,
    SystemStatus,
    ErrorResponse,
)
from model_manager import ModelManager
from inference_engine import InferenceEngineFactory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


# 全局变量
model_manager: Optional[ModelManager] = None
config: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global model_manager, config
    
    # 启动时初始化
    logger.info("正在启动模型推理服务...")
    
    # 加载配置
    config = load_config()
    
    # 创建模型管理器
    use_mock = config.get("engine", {}).get("use_mock", True)
    model_manager = ModelManager(use_mock_engine=use_mock)
    
    # 预加载配置的模型
    models_config = config.get("models", [])
    for model_cfg in models_config:
        if model_cfg.get("auto_load", False):
            model_config = ModelConfig(
                model_name=model_cfg["name"],
                model_path=model_cfg["path"],
                model_format=model_cfg.get("format", "pytorch"),
                quantization=model_cfg.get("quantization", "none"),
                max_model_len=model_cfg.get("max_model_len"),
                gpu_memory_utilization=model_cfg.get("gpu_memory_utilization", 0.9),
                tensor_parallel_size=model_cfg.get("tensor_parallel_size", 1),
                dtype=model_cfg.get("dtype", "auto"),
            )
            await model_manager.load_model(model_config)
    
    logger.info("模型推理服务启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭模型推理服务...")
    if model_manager:
        await model_manager.shutdown()
    logger.info("模型推理服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="本地模型推理服务",
    description="OpenAI 兼容的本地大模型推理 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="内部服务器错误",
            code=500,
            details={"message": str(exc)},
        ).model_dump(),
    )


# ==================== OpenAI 兼容 API ====================

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """聊天补全接口 (OpenAI 兼容)
    
    与 OpenAI Chat Completions API 完全兼容
    """
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    # 获取推理引擎
    engine = model_manager.get_engine(request.model)
    if not engine:
        raise HTTPException(
            status_code=404,
            detail=f"模型 {request.model} 未加载或不存在",
        )
    
    try:
        if request.stream:
            # 流式输出
            async def generate():
                async for chunk in engine.chat_completion_stream(request):
                    yield f"data: {chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )
        else:
            # 非流式输出
            response = await engine.chat_completion(request)
            return response
            
    except Exception as e:
        logger.error(f"聊天补全失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions", response_model=CompletionResponse)
async def completions(request: CompletionRequest):
    """文本补全接口 (OpenAI 兼容)
    
    与 OpenAI Completions API 完全兼容
    """
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    # 获取推理引擎
    engine = model_manager.get_engine(request.model)
    if not engine:
        raise HTTPException(
            status_code=404,
            detail=f"模型 {request.model} 未加载或不存在",
        )
    
    try:
        if request.stream:
            # 流式输出
            async def generate():
                async for chunk in engine.completion_stream(request):
                    yield f"data: {chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )
        else:
            # 非流式输出
            response = await engine.completion(request)
            return response
            
    except Exception as e:
        logger.error(f"文本补全失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 模型管理 API ====================

@app.get("/v1/models")
async def list_models():
    """列出所有可用模型"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    models = model_manager.list_models()
    return {
        "object": "list",
        "data": [model.model_dump() for model in models],
    }


@app.post("/v1/models/load")
async def load_model(config: ModelConfig):
    """加载模型"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    success = await model_manager.load_model(config)
    if success:
        return {"status": "success", "message": f"模型 {config.model_name} 已加载"}
    else:
        raise HTTPException(status_code=500, detail=f"加载模型 {config.model_name} 失败")


@app.post("/v1/models/{model_name}/unload")
async def unload_model(model_name: str):
    """卸载模型"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    success = await model_manager.unload_model(model_name)
    if success:
        return {"status": "success", "message": f"模型 {model_name} 已卸载"}
    else:
        raise HTTPException(status_code=404, detail=f"模型 {model_name} 不存在或卸载失败")


@app.get("/v1/models/{model_name}/info")
async def get_model_info(model_name: str):
    """获取模型详细信息"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    info = model_manager.get_model_info(model_name)
    if info:
        return info.model_dump()
    else:
        raise HTTPException(status_code=404, detail=f"模型 {model_name} 不存在")


# ==================== 系统 API ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/v1/system/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    if not model_manager:
        raise HTTPException(status_code=503, detail="服务未就绪")
    
    return model_manager.get_system_status()


@app.get("/v1/system/engines")
async def get_available_engines():
    """获取可用的推理引擎"""
    return {
        "engines": InferenceEngineFactory.get_available_engines(),
    }


@app.get("/v1/system/quantization-methods")
async def get_quantization_methods():
    """获取支持的量化方法"""
    from quantizer import QuantizerFactory
    return {
        "methods": QuantizerFactory.get_supported_methods(),
    }


# ==================== 主函数 ====================

def main():
    """启动服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="本地模型推理服务")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    parser.add_argument("--workers", type=int, default=1, help="Worker 数量")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    
    args = parser.parse_args()
    
    # 更新全局配置路径
    global config
    config = load_config(args.config)
    
    # 启动服务
    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()