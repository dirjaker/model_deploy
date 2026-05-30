"""
模型管理模块
负责模型的加载/卸载、显存监控、多模型切换
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from models import ModelConfig, ModelInfo, SystemStatus
from inference_engine import (
    BaseInferenceEngine,
    InferenceEngineFactory,
    EngineStatus,
)

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """模型状态"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class ModelState:
    """模型状态"""
    config: ModelConfig
    engine: Optional[BaseInferenceEngine] = None
    status: ModelStatus = ModelStatus.UNLOADED
    load_time: Optional[float] = None
    last_used: Optional[float] = None
    request_count: int = 0
    error_message: Optional[str] = None


class GPUMemoryMonitor:
    """GPU 显存监控"""
    
    def __init__(self):
        self.logger = logging.getLogger("GPUMemoryMonitor")
    
    def get_memory_info(self) -> Dict[str, float]:
        """获取 GPU 显存信息
        
        实际实现需要 torch.cuda 或 pynvml
        """
        # 模拟模式
        return {
            "total": 24.0,  # 总显存 (GB)
            "used": 0.0,    # 已使用显存 (GB)
            "free": 24.0,   # 空闲显存 (GB)
            "utilization": 0.0,  # 利用率 (%)
        }
        
        # 实际实现
        # import torch
        # if torch.cuda.is_available():
        #     total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        #     used = torch.cuda.memory_allocated(0) / 1024**3
        #     free = total - used
        #     return {
        #         "total": round(total, 2),
        #         "used": round(used, 2),
        #         "free": round(free, 2),
        #         "utilization": round(used / total * 100, 2),
        #     }
        # return {"total": 0, "used": 0, "free": 0, "utilization": 0}
    
    def estimate_model_memory(self, model_config: ModelConfig) -> float:
        """估算模型显存需求 (GB)"""
        # 简单估算公式
        # 实际显存需求取决于模型大小、量化方式等
        base_memory = 7.0  # 基础 7B 模型约 7GB
        
        if model_config.quantization == "gptq" or model_config.quantization == "awq":
            base_memory *= 0.25  # 4-bit 量化后约 1/4
        elif model_config.quantization == "gguf":
            base_memory *= 0.3
        
        return base_memory


class ModelManager:
    """模型管理器
    
    管理多个模型的加载、卸载和调度
    """
    
    def __init__(self, use_mock_engine: bool = True):
        self.models: Dict[str, ModelState] = {}
        self.memory_monitor = GPUMemoryMonitor()
        self.use_mock_engine = use_mock_engine
        self.logger = logging.getLogger("ModelManager")
        self._lock = asyncio.Lock()
        self._start_time = time.time()
    
    async def load_model(self, config: ModelConfig) -> bool:
        """加载模型
        
        Args:
            config: 模型配置
            
        Returns:
            是否加载成功
        """
        model_name = config.model_name
        
        async with self._lock:
            # 检查模型是否已加载
            if model_name in self.models:
                state = self.models[model_name]
                if state.status == ModelStatus.READY:
                    self.logger.warning(f"模型 {model_name} 已加载")
                    return True
                elif state.status == ModelStatus.LOADING:
                    self.logger.warning(f"模型 {model_name} 正在加载中")
                    return False
            
            # 检查显存
            memory_info = self.memory_monitor.get_memory_info()
            model_memory = self.memory_monitor.estimate_model_memory(config)
            
            if memory_info["free"] < model_memory:
                self.logger.error(
                    f"显存不足: 需要 {model_memory:.1f}GB, "
                    f"可用 {memory_info['free']:.1f}GB"
                )
                return False
            
            # 创建模型状态
            self.models[model_name] = ModelState(
                config=config,
                status=ModelStatus.LOADING,
            )
        
        try:
            self.logger.info(f"开始加载模型: {model_name}")
            start_time = time.time()
            
            # 创建推理引擎
            engine = InferenceEngineFactory.create(config, use_mock=self.use_mock_engine)
            
            # 初始化引擎
            await engine.initialize()
            
            # 更新状态
            async with self._lock:
                state = self.models[model_name]
                state.engine = engine
                state.status = ModelStatus.READY
                state.load_time = time.time() - start_time
            
            self.logger.info(f"模型 {model_name} 加载完成，耗时 {state.load_time:.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型 {model_name} 失败: {e}")
            async with self._lock:
                state = self.models[model_name]
                state.status = ModelStatus.ERROR
                state.error_message = str(e)
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """卸载模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否卸载成功
        """
        async with self._lock:
            if model_name not in self.models:
                self.logger.warning(f"模型 {model_name} 不存在")
                return False
            
            state = self.models[model_name]
            if state.status != ModelStatus.READY:
                self.logger.warning(f"模型 {model_name} 状态异常: {state.status.value}")
                return False
            
            state.status = ModelStatus.UNLOADING
        
        try:
            self.logger.info(f"开始卸载模型: {model_name}")
            
            # 关闭引擎
            if state.engine:
                await state.engine.shutdown()
            
            # 更新状态
            async with self._lock:
                del self.models[model_name]
            
            self.logger.info(f"模型 {model_name} 已卸载")
            return True
            
        except Exception as e:
            self.logger.error(f"卸载模型 {model_name} 失败: {e}")
            async with self._lock:
                state.status = ModelStatus.ERROR
                state.error_message = str(e)
            return False
    
    def get_engine(self, model_name: str) -> Optional[BaseInferenceEngine]:
        """获取模型的推理引擎
        
        Args:
            model_name: 模型名称
            
        Returns:
            推理引擎实例，如果模型未加载则返回 None
        """
        if model_name not in self.models:
            return None
        
        state = self.models[model_name]
        if state.status != ModelStatus.READY:
            return None
        
        # 更新使用时间
        state.last_used = time.time()
        state.request_count += 1
        
        return state.engine
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        if model_name not in self.models:
            return None
        
        state = self.models[model_name]
        return ModelInfo(
            model_name=model_name,
            model_path=state.config.model_path,
            model_format=state.config.model_format,
            is_loaded=state.status == ModelStatus.READY,
            gpu_memory_used=self.memory_monitor.estimate_model_memory(state.config),
            max_model_len=state.config.max_model_len or 4096,
            active_requests=state.engine.metrics.active_requests if state.engine else 0,
        )
    
    def list_models(self) -> List[ModelInfo]:
        """列出所有模型"""
        models = []
        for model_name in self.models:
            info = self.get_model_info(model_name)
            if info:
                models.append(info)
        return models
    
    def get_system_status(self) -> SystemStatus:
        """获取系统状态"""
        memory_info = self.memory_monitor.get_memory_info()
        
        loaded_count = sum(
            1 for state in self.models.values()
            if state.status == ModelStatus.READY
        )
        
        total_active_requests = sum(
            state.engine.metrics.active_requests
            for state in self.models.values()
            if state.engine
        )
        
        total_requests = sum(
            state.request_count
            for state in self.models.values()
        )
        
        return SystemStatus(
            models_loaded=loaded_count,
            gpu_memory_total=memory_info["total"],
            gpu_memory_used=memory_info["used"],
            gpu_memory_free=memory_info["free"],
            active_requests=total_active_requests,
            total_requests=total_requests,
            uptime=time.time() - self._start_time,
        )
    
    async def switch_model(self, from_model: str, to_config: ModelConfig) -> bool:
        """切换模型
        
        Args:
            from_model: 当前模型名称
            to_config: 新模型配置
            
        Returns:
            是否切换成功
        """
        self.logger.info(f"切换模型: {from_model} -> {to_config.model_name}")
        
        # 卸载当前模型
        if from_model in self.models:
            success = await self.unload_model(from_model)
            if not success:
                self.logger.error(f"卸载模型 {from_model} 失败")
                return False
        
        # 加载新模型
        success = await self.load_model(to_config)
        if not success:
            self.logger.error(f"加载模型 {to_config.model_name} 失败")
            return False
        
        self.logger.info(f"模型切换完成: {to_config.model_name}")
        return True
    
    async def cleanup_idle_models(self, max_idle_time: float = 3600) -> List[str]:
        """清理空闲模型
        
        Args:
            max_idle_time: 最大空闲时间（秒）
            
        Returns:
            被清理的模型列表
        """
        current_time = time.time()
        models_to_unload = []
        
        for model_name, state in self.models.items():
            if state.status == ModelStatus.READY and state.last_used:
                idle_time = current_time - state.last_used
                if idle_time > max_idle_time:
                    models_to_unload.append(model_name)
        
        unloaded = []
        for model_name in models_to_unload:
            success = await self.unload_model(model_name)
            if success:
                unloaded.append(model_name)
        
        if unloaded:
            self.logger.info(f"清理了 {len(unloaded)} 个空闲模型: {unloaded}")
        
        return unloaded
    
    async def shutdown(self) -> None:
        """关闭所有模型"""
        self.logger.info("关闭所有模型...")
        
        model_names = list(self.models.keys())
        for model_name in model_names:
            await self.unload_model(model_name)
        
        self.logger.info("所有模型已关闭")