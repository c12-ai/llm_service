"""
配置文件 - LLM Service
支持环境变量配置，方便快速切换模型
"""
import os

# ============================================
# 模型配置
# ============================================
# 支持的常用模型（取消注释对应的 MODEL_PATH 环境变量即可切换）:
# - Qwen3-4B: 小模型，快速测试
# - Qwen2.5-7B-Instruct: 推荐，平衡性能和质量
# - Qwen2.5-14B-Instruct: 更强性能
# - Qwen2.5-32B-Instruct: 旗舰模型

MODEL_PATH = os.getenv(
    "MODEL_PATH", 
    "/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen3-4B"
)
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen3-4B")

# ============================================
# 服务配置
# ============================================
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8000"))

# vLLM 配置 (用于GPU环境)
VLLM_CONFIG = {
    "tensor_parallel_size": int(os.getenv("TENSOR_PARALLEL_SIZE", "1")),  # GPU数量
    "gpu_memory_utilization": float(os.getenv("GPU_MEMORY_UTILIZATION", "0.9")),
    "max_model_len": int(os.getenv("MAX_MODEL_LEN", "4096")),
    "trust_remote_code": True,
}

# 生成参数默认值
# DEFAULT_GENERATION_CONFIG = {
#     "max_tokens": 512,
#     "temperature": 0.7,
#     "top_p": 0.9,
#     "top_k": 50,
# }
