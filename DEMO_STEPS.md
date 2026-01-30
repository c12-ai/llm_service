# 🎬 Docker 部署演示 - 本地测试步骤

## 📝 完整流程（3分钟搞定）

### 步骤 1: 准备环境 (30秒)

```bash
# 检查 Docker 是否安装
docker --version
docker ps

# 如果未安装，请先安装 Docker Desktop:
# macOS: https://www.docker.com/products/docker-desktop
# Linux: curl -fsSL https://get.docker.com | sh
```

### 步骤 2: 下载模型 (1-2分钟，仅首次需要)

```bash
# 安装 modelscope
pip install modelscope

# 下载 Qwen3-4B 模型（约 8GB，可能需要几分钟）
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"

# 确认模型已下载
ls -lh ~/.cache/modelscope/hub/models/Qwen/Qwen3-4B
```

### 步骤 3: 一键部署 (1-2分钟)

```bash
# 进入项目目录
cd /Users/tengpi/vs_code/llm_service

# 运行一键部署脚本
./deploy-cpu.sh
```

你会看到：
```
==========================================
🚀 LLM Service Docker 部署 (CPU版本)
==========================================

📦 步骤 1/4: 构建 Docker 镜像...
🚀 步骤 2/4: 启动服务...
⏳步骤 3/4: 等待服务启动（模型加载中）...
✅ 服务启动成功！
🧪 步骤 4/4: 测试 API...
✅ API 测试成功！

==========================================
🎉 部署完成！
==========================================
```

### 步骤 4: 运行测试 (30秒)

```bash
# 运行完整测试套件
./test-docker.sh
```

你会看到：
```
==========================================
🧪 LLM Service Docker 测试
==========================================

测试 1/5: 健康检查...
  ✅ 健康检查通过

测试 2/5: 非流式对话...
  ✅ 非流式对话成功
  模型回答: 2

测试 3/5: 多轮对话（带历史）...
  ✅ 多轮对话成功
  模型回答: 你叫小明

测试 4/5: 流式输出...
  ✅ 流式输出成功

测试 5/5: OpenAI SDK 兼容性...
  ✅ OpenAI SDK 测试成功

==========================================
🎉 所有测试通过！
==========================================
```

### 步骤 5: 实际使用 (随时)

#### 5.1 使用 curl 测试

```bash
# 简单对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "system", "content": "你是一个简洁的助手"},
      {"role": "user", "content": "1+1等于几？"}
    ],
    "max_tokens": 50
  }'
```

预期响应：
```json
{
  "id": "chatcmpl-abc12345",
  "object": "chat.completion",
  "created": 1706524800,
  "model": "Qwen3-4B",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "2"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 3,
    "total_tokens": 28
  }
}
```

#### 5.2 使用 Python OpenAI SDK

创建文件 `test_my_service.py`:

```python
import openai

# 配置指向本地服务
client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

# 测试1: 简单对话
print("测试1: 简单对话")
response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "user", "content": "用一句话介绍Python"}
    ],
    max_tokens=100
)
print(f"回答: {response.choices[0].message.content}\n")

# 测试2: 流式输出
print("测试2: 流式输出")
print("模型回答: ", end="", flush=True)
stream = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "数到5"}],
    max_tokens=50,
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n")

# 测试3: 多轮对话
print("测试3: 多轮对话（带历史）")
response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "你好，小明！"},
        {"role": "user", "content": "我叫什么？"}
    ],
    max_tokens=30
)
print(f"回答: {response.choices[0].message.content}")
print(f"Token 使用: {response.usage.total_tokens}")
```

运行：
```bash
python test_my_service.py
```

#### 5.3 访问 API 文档

浏览器打开：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 步骤 6: 查看日志和状态

```bash
# 实时查看日志
docker logs -f qwen-llm-service-cpu

# 查看资源使用
docker stats qwen-llm-service-cpu

# 查看容器状态
docker ps | grep qwen
```

### 步骤 7: 停止服务

```bash
# 停止并删除容器
docker-compose -f docker-compose.cpu.yml down

# 或者只停止（保留容器）
docker stop qwen-llm-service-cpu
```

## 🎯 总结：你已经完成了

✅ Docker 镜像构建  
✅ 容器化部署  
✅ 服务启动和健康检查  
✅ API 测试（非流式 + 流式）  
✅ OpenAI SDK 兼容性验证  

## 📋 快速命令参考

```bash
# 查看所有可用命令
./docker-quick-ref.sh

# 部署
./deploy-cpu.sh

# 测试
./test-docker.sh

# 日志
docker logs -f qwen-llm-service-cpu

# 停止
docker-compose -f docker-compose.cpu.yml down

# 重启
docker-compose -f docker-compose.cpu.yml restart
```

## 🚀 下一步

现在你的服务已经在本地运行了，可以：

1. **集成到其他项目**
   - 修改客户端的 `base_url` 为 `http://localhost:8000/v1`
   - 完全兼容 OpenAI API，无需修改其他代码

2. **切换到 GPU 版本**（如果有 GPU）
   ```bash
   docker-compose up -d  # 使用 GPU 版本配置
   ```

3. **部署到服务器**
   - 修改 `docker-compose.cpu.yml` 中的端口映射
   - 使用 Nginx 反向代理
   - 添加 HTTPS 证书

4. **扩展功能**
   - 添加 API Key 认证
   - 集成 Prometheus 监控
   - 实现多模型切换
   - 添加请求队列和限流

## 📖 更多资源

- [Docker 详细部署指南](DOCKER_DEPLOYMENT.md)
- [OpenAI API 兼容性说明](OPENAI_COMPATIBILITY.md)
- [项目 README](README.md)

---

**恭喜！** 你已经成功部署并测试了基于 Docker 的 LLM 服务！🎉
