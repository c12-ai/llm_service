# Dockerfile for vLLM-based Qwen LLM Service
# 支持GPU部署

# 使用vLLM官方镜像作为基础镜像
FROM vllm/vllm-openai:latest

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY config.py .
COPY llm_service.py .

# 设置环境变量
ENV MODEL_PATH=/models
ENV SERVICE_HOST=0.0.0.0
ENV SERVICE_PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 重置ENTRYPOINT（vLLM基础镜像可能设置了ENTRYPOINT）
ENTRYPOINT []

# 启动服务
CMD ["python", "llm_service.py"]
