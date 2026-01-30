"""
CPU版本的LLM Service - 用于本地无GPU环境测试
基于transformers库，完全兼容 OpenAI API
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from contextlib import asynccontextmanager
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from threading import Thread
import time
import json
import uuid
import config
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局模型和tokenizer
model = None
tokenizer = None


# 请求模型
class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="输入文本提示")
    max_tokens: int = Field(512, ge=1, le=2048, description="生成的最大token数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="采样温度")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="nucleus采样参数")
    top_k: int = Field(50, ge=1, description="top-k采样参数")


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: system/user/assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """OpenAI 兼容的聊天请求"""
    model: Optional[str] = Field(None, description="模型名称（可选，服务端只有一个模型）")
    messages: List[ChatMessage] = Field(..., description="对话历史")
    max_tokens: Optional[int] = Field(512, ge=1, le=4096, description="生成的最大token数")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="采样温度")
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="nucleus采样参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="存在惩罚（暂不支持）")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="频率惩罚（暂不支持）")
    n: Optional[int] = Field(1, ge=1, le=1, description="生成数量（仅支持1）")
    user: Optional[str] = Field(None, description="用户标识")


# 响应模型
class GenerationResponse(BaseModel):
    text: str
    prompt: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载模型"""
    global model, tokenizer
    try:
        logger.info(f"正在加载模型: {config.MODEL_PATH}")
        logger.warning("⚠️  CPU模式运行，速度较慢，仅用于测试！")

        tokenizer = AutoTokenizer.from_pretrained(
            config.MODEL_PATH,
            trust_remote_code=True
        )

        # CPU模式，使用较低精度以节省内存
        model = AutoModelForCausalLM.from_pretrained(
            config.MODEL_PATH,
            torch_dtype=torch.float16,  # 使用fp16节省内存
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True,  # 低内存模式
        )

        logger.info("✅ 模型加载成功（CPU模式）")
        yield
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {str(e)}")
        logger.info("提示: 如果内存不足，请尝试使用更小的模型（如Qwen2.5-7B）")
        raise


# FastAPI应用
app = FastAPI(
    title="Qwen LLM Service (CPU版本)",
    description="基于transformers的Qwen大模型推理服务（CPU版本，用于测试）",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """健康检查"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    return {
        "status": "healthy",
        "model": config.MODEL_PATH,
        "device": "cpu",
        "warning": "CPU模式运行，速度较慢"
    }


@app.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """文本生成接口"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        # Tokenize输入
        inputs = tokenizer(request.prompt, return_tensors="pt")
        
        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # 解码输出
        generated_text = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return GenerationResponse(
            text=generated_text,
            prompt=request.prompt
        )
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI 完全兼容的聊天接口"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        # 使用tokenizer的chat template（如果支持）
        if hasattr(tokenizer, 'apply_chat_template'):
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # 手动构建prompt
            prompt = ""
            for msg in request.messages:
                if msg.role == "system":
                    prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
                elif msg.role == "user":
                    prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
                elif msg.role == "assistant":
                    prompt += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"
            prompt += "<|im_start|>assistant\n"
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt")
        input_token_count = inputs['input_ids'].shape[1]
        
        # 处理停止词
        stop_sequences = []
        if request.stop:
            if isinstance(request.stop, str):
                stop_sequences = [request.stop]
            else:
                stop_sequences = request.stop
        
        # 流式输出
        if request.stream:
            return StreamingResponse(
                stream_chat_completions(
                    inputs=inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    stop_sequences=stop_sequences,
                    model_name=request.model or config.MODEL_NAME,
                    input_token_count=input_token_count
                ),
                media_type="text/event-stream"
            )
        
        # 非流式输出
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # 解码
        generated_text = tokenizer.decode(
            outputs[0][input_token_count:],
            skip_special_tokens=True
        )
        
        # 处理停止词
        if stop_sequences:
            for stop_seq in stop_sequences:
                if stop_seq in generated_text:
                    generated_text = generated_text[:generated_text.index(stop_seq)]
                    break
        
        # 统计输出 tokens
        output_token_count = len(tokenizer.encode(generated_text, add_special_tokens=False))
        
        # 返回 OpenAI 兼容格式
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model or config.MODEL_NAME,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": generated_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": input_token_count,
                "completion_tokens": output_token_count,
                "total_tokens": input_token_count + output_token_count
            }
        }
    except Exception as e:
        logger.error(f"聊天生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def stream_chat_completions(
    inputs,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
    stop_sequences: List[str],
    model_name: str,
    input_token_count: int
):
    """流式生成聊天响应（OpenAI 兼容）"""
    try:
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": True,
            "pad_token_id": tokenizer.eos_token_id,
            "streamer": streamer,
        }
        
        # 在后台线程中生成
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        created_time = int(time.time())
        
        # 流式返回
        for text in streamer:
            # 检查停止词
            should_stop = False
            for stop_seq in stop_sequences:
                if stop_seq in text:
                    text = text[:text.index(stop_seq)]
                    should_stop = True
                    break
            
            chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": text
                    },
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            if should_stop:
                break
        
        # 发送结束标记
        final_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": model_name,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
        
        thread.join()
        
    except Exception as e:
        logger.error(f"流式生成失败: {str(e)}")
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": 500
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        log_level="info"
    )
