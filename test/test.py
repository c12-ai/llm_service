from modelscope import AutoModelForCausalLM, AutoTokenizer

# 加载原始模型（默认高精度）
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-8B",
    device_map="auto",
    trust_remote_code=True
)
print(model.dtype)  # 通常输出 torch.bfloat16 或 torch.float16