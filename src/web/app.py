"""
Web Dashboard for Model Deploy
Provides a management dashboard for model deployment and inference.
"""
import sys
import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models import ModelConfig, ModelInfo, SystemStatus
from model_manager import ModelManager
from inference_engine import InferenceEngineFactory

# Global state
model_manager: Optional[ModelManager] = None

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_manager
    model_manager = ModelManager(use_mock_engine=True)
    yield
    if model_manager:
        await model_manager.shutdown()


app = FastAPI(
    title="Model Deploy Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/models")
async def list_models():
    if not model_manager:
        raise HTTPException(503, "Service not ready")
    models = model_manager.list_models()
    return [m.model_dump() for m in models]


class LoadModelRequest(BaseModel):
    model_name: str
    model_path: str = "local-model"
    model_format: str = "pytorch"
    quantization: str = "none"
    max_model_len: Optional[int] = 4096
    gpu_memory_utilization: float = 0.9


@app.post("/api/models/load")
async def load_model(req: LoadModelRequest):
    if not model_manager:
        raise HTTPException(503, "Service not ready")
    config = ModelConfig(
        model_name=req.model_name,
        model_path=req.model_path,
        model_format=req.model_format,
        quantization=req.quantization,
        max_model_len=req.max_model_len,
        gpu_memory_utilization=req.gpu_memory_utilization,
    )
    success = await model_manager.load_model(config)
    if success:
        return {"status": "success", "message": f"Model {req.model_name} loaded"}
    raise HTTPException(500, f"Failed to load model {req.model_name}")


@app.post("/api/models/{model_name}/unload")
async def unload_model(model_name: str):
    if not model_manager:
        raise HTTPException(503, "Service not ready")
    success = await model_manager.unload_model(model_name)
    if success:
        return {"status": "success", "message": f"Model {model_name} unloaded"}
    raise HTTPException(404, f"Model {model_name} not found")


@app.get("/api/system/status")
async def system_status():
    if not model_manager:
        raise HTTPException(503, "Service not ready")
    return model_manager.get_system_status().model_dump()


@app.get("/api/system/engines")
async def available_engines():
    return {"engines": InferenceEngineFactory.get_available_engines()}


class ChatRequest(BaseModel):
    model: str
    message: str
    temperature: float = 0.7
    max_tokens: int = 200


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not model_manager:
        raise HTTPException(503, "Service not ready")
    engine = model_manager.get_engine(req.model)
    if not engine:
        raise HTTPException(404, f"Model {req.model} not loaded")
    from models import ChatCompletionRequest, ChatMessage
    chat_req = ChatCompletionRequest(
        model=req.model,
        messages=[ChatMessage(role="user", content=req.message)],
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    response = await engine.chat_completion(chat_req)
    return {
        "response": response.choices[0].message.content,
        "usage": response.usage.model_dump(),
    }


def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
