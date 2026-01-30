"""
vLLM FastAPI Service for Qwen-32B
用于GPU环境的生产部署
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
from vllm import LLM, SamplingParams
from vllm.utils import random_uuid
import config
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI应用
app = FastAPI(
    title="Qwen LLM Service (vLLM)",
    description="基于vLLM的Qwen大模型推理服务",
    version="1.0.0"
)

# 全局模型实例
llm_engine: Optional[LLM] = None


# 请求模型
class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="输入文本提示")
    max_tokens: int = Field(512, ge=1, le=4096, description="生成的最大token数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="采样温度")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="nucleus采样参数")
    top_k: int = Field(50, ge=-1, description="top-k采样参数")
    stop: Optional[List[str]] = Field(None, description="停止词列表")
    stream: bool = Field(False, description="是否流式输出")


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: system/user/assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话历史")
    max_tokens: int = Field(512, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    stream: bool = Field(False, description="是否流式输出")


# 响应模型
class GenerationResponse(BaseModel):
    id: str
    text: str
    prompt: str
    finish_reason: str


@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    global llm_engine
    try:
        logger.info(f"正在加载模型: {config.MODEL_PATH}")
        llm_engine = LLM(
            model=config.MODEL_PATH,
            tensor_parallel_size=config.VLLM_CONFIG["tensor_parallel_size"],
            gpu_memory_utilization=config.VLLM_CONFIG["gpu_memory_utilization"],
            max_model_len=config.VLLM_CONFIG["max_model_len"],
            trust_remote_code=config.VLLM_CONFIG["trust_remote_code"],
        )
        logger.info("模型加载成功！")
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        raise


@app.get("/health")
async def health_check():
    """健康检查"""
    if llm_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    return {"status": "healthy", "model": config.MODEL_PATH}


@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """文本生成接口（非流式）"""
    if llm_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        sampling_params = SamplingParams(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stop=request.stop,
        )
        
        outputs = llm_engine.generate([request.prompt], sampling_params)
        output = outputs[0]
        
        return GenerationResponse(
            id=random_uuid(),
            text=output.outputs[0].text,
            prompt=request.prompt,
            finish_reason=output.outputs[0].finish_reason
        )
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI兼容的聊天接口"""
    if llm_engine is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        # 将messages转换为prompt（简化版，实际需要按模型格式）
        prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
            elif msg.role == "user":
                prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
            elif msg.role == "assistant":
                prompt += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
        )
        
        if request.stream:
            # 流式输出暂不实现，返回提示
            raise HTTPException(status_code=501, detail="流式输出暂未实现")
        
        outputs = llm_engine.generate([prompt], sampling_params)
        output = outputs[0]
        
        return {
            "id": random_uuid(),
            "object": "chat.completion",
            "created": 0,
            "model": config.MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": output.outputs[0].text
                },
                "finish_reason": output.outputs[0].finish_reason
            }]
        }
    except Exception as e:
        logger.error(f"聊天生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        log_level="info"
    )
