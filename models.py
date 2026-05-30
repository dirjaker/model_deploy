"""
数据模型定义
用于模型配置、推理请求和推理响应
"""
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
import time
import uuid


class ModelFormat(str, Enum):
    """支持的模型格式"""
    PYTORCH = "pytorch"
    GPTQ = "gptq"
    AWQ = "awq"
    GGUF = "gguf"
    TENSORRT = "tensorrt"


class QuantizationMethod(str, Enum):
    """量化方法"""
    GPTQ = "gptq"
    AWQ = "awq"
    GGUF = "gguf"
    NONE = "none"


class ModelConfig(BaseModel):
    """模型配置"""
    model_name: str = Field(..., description="模型名称")
    model_path: str = Field(..., description="模型路径或HuggingFace ID")
    model_format: ModelFormat = Field(ModelFormat.PYTORCH, description="模型格式")
    quantization: QuantizationMethod = Field(QuantizationMethod.NONE, description="量化方法")
    max_model_len: Optional[int] = Field(None, description="最大序列长度")
    gpu_memory_utilization: float = Field(0.9, description="GPU显存利用率")
    tensor_parallel_size: int = Field(1, description="张量并行数")
    dtype: str = Field("auto", description="数据类型 (auto, float16, bfloat16)")
    trust_remote_code: bool = Field(False, description="是否信任远程代码")
    
    class Config:
        use_enum_values = True


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色 (system, user, assistant)")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="发送者名称")


class ChatCompletionRequest(BaseModel):
    """聊天补全请求 (OpenAI 兼容)"""
    model: str = Field(..., description="模型名称")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    temperature: float = Field(0.7, description="采样温度", ge=0, le=2)
    top_p: float = Field(1.0, description="核采样概率", ge=0, le=1)
    n: int = Field(1, description="生成选项数量", ge=1)
    stream: bool = Field(False, description="是否流式输出")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")
    presence_penalty: float = Field(0.0, description="存在惩罚", ge=-2, le=2)
    frequency_penalty: float = Field(0.0, description="频率惩罚", ge=-2, le=2)
    user: Optional[str] = Field(None, description="用户标识")


class CompletionRequest(BaseModel):
    """文本补全请求 (OpenAI 兼容)"""
    model: str = Field(..., description="模型名称")
    prompt: Union[str, List[str]] = Field(..., description="提示文本")
    temperature: float = Field(0.7, description="采样温度", ge=0, le=2)
    top_p: float = Field(1.0, description="核采样概率", ge=0, le=1)
    n: int = Field(1, description="生成选项数量", ge=1)
    stream: bool = Field(False, description="是否流式输出")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    max_tokens: Optional[int] = Field(None, description="最大生成token数")
    presence_penalty: float = Field(0.0, description="存在惩罚", ge=-2, le=2)
    frequency_penalty: float = Field(0.0, description="频率惩罚", ge=-2, le=2)
    user: Optional[str] = Field(None, description="用户标识")


class Usage(BaseModel):
    """Token使用统计"""
    prompt_tokens: int = Field(0, description="提示token数")
    completion_tokens: int = Field(0, description="补全token数")
    total_tokens: int = Field(0, description="总token数")


class ChatChoice(BaseModel):
    """聊天补全选项"""
    index: int = Field(0, description="选项索引")
    message: ChatMessage = Field(..., description="消息内容")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class CompletionChoice(BaseModel):
    """文本补全选项"""
    index: int = Field(0, description="选项索引")
    text: str = Field(..., description="生成文本")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class ChatCompletionResponse(BaseModel):
    """聊天补全响应 (OpenAI 兼容)"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}", description="响应ID")
    object: str = Field("chat.completion", description="对象类型")
    created: int = Field(default_factory=lambda: int(time.time()), description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[ChatChoice] = Field(..., description="补全选项列表")
    usage: Usage = Field(default_factory=Usage, description="Token使用统计")


class CompletionResponse(BaseModel):
    """文本补全响应 (OpenAI 兼容)"""
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex[:12]}", description="响应ID")
    object: str = Field("text_completion", description="对象类型")
    created: int = Field(default_factory=lambda: int(time.time()), description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[CompletionChoice] = Field(..., description="补全选项列表")
    usage: Usage = Field(default_factory=Usage, description="Token使用统计")


class StreamChoice(BaseModel):
    """流式输出选项"""
    index: int = Field(0, description="选项索引")
    delta: Dict[str, Any] = Field(..., description="增量内容")
    finish_reason: Optional[str] = Field(None, description="结束原因")


class StreamResponse(BaseModel):
    """流式输出响应"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}", description="响应ID")
    object: str = Field("chat.completion.chunk", description="对象类型")
    created: int = Field(default_factory=lambda: int(time.time()), description="创建时间戳")
    model: str = Field(..., description="模型名称")
    choices: List[StreamChoice] = Field(..., description="选项列表")


class ModelInfo(BaseModel):
    """模型信息"""
    model_name: str = Field(..., description="模型名称")
    model_path: str = Field(..., description="模型路径")
    model_format: str = Field(..., description="模型格式")
    is_loaded: bool = Field(False, description="是否已加载")
    gpu_memory_used: float = Field(0.0, description="GPU显存使用 (GB)")
    max_model_len: int = Field(4096, description="最大序列长度")
    active_requests: int = Field(0, description="活跃请求数")


class SystemStatus(BaseModel):
    """系统状态"""
    models_loaded: int = Field(0, description="已加载模型数")
    gpu_memory_total: float = Field(0.0, description="总GPU显存 (GB)")
    gpu_memory_used: float = Field(0.0, description="已使用GPU显存 (GB)")
    gpu_memory_free: float = Field(0.0, description="空闲GPU显存 (GB)")
    active_requests: int = Field(0, description="活跃请求数")
    total_requests: int = Field(0, description="总请求数")
    uptime: float = Field(0.0, description="运行时间 (秒)")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    code: int = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")