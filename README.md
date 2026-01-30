# Qwen LLM Service

基于 Qwen 大模型的推理服务，**完全兼容 OpenAI API**，支持 CPU 和 GPU 部署。

## ✨ 特性

- ✅ **OpenAI API 完全兼容** - 无缝替换 OpenAI 服务
- ✅ **流式输出支持** - 实时返回生成内容
- ✅ **多种部署方式** - 本地/Docker/GPU/CPU
- ✅ **Token 统计** - 完整的使用量统计
- ✅ **生产就绪** - 健康检查、错误处理、日志记录

## 🚀 快速开始

### 方式1: Docker 部署（推荐）⭐

```bash
# 1. 下载模型
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"

# 2. 一键部署
./deploy-cpu.sh

# 3. 测试服务
./test-docker.sh
```

详见：[Docker 快速开始](DOCKER_QUICKSTART.md)

### 方式2: 本地运行（开发测试）

```bash
# 1. 安装依赖
pip install -r requirements-cpu.txt

# 2. 下载模型
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"

# 3. 启动服务
python llm_service_cpu.py

# 4. 测试
python test_openai_compatibility.py
```

## 📖 文档

| 文档 | 说明 |
|------|------|
| [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | Docker 快速开始（推荐） |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker 详细部署指南 |
| [MODEL_SWITCH.md](MODEL_SWITCH.md) | **模型快速切换指南** ⭐ |
| [OPENAI_COMPATIBILITY.md](OPENAI_COMPATIBILITY.md) | OpenAI API 兼容性说明 |

## 🔄 快速切换模型

只需 3 步，无需修改代码：

```bash
# 1. 复制配置模板（首次）
cp .env.example .env

# 2. 编辑 .env，修改模型路径
# MODEL_PATH=/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct
# MODEL_NAME=Qwen2.5-7B-Instruct

# 3. 重启服务
docker-compose -f docker-compose.cpu.yml restart
```

详见：[MODEL_SWITCH.md](MODEL_SWITCH.md)
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker 详细部署指南 |
| [OPENAI_COMPATIBILITY.md](OPENAI_COMPATIBILITY.md) | OpenAI API 兼容性说明 |

## 🔧 使用示例

### Python (OpenAI SDK)

```python
import openai

client = openai.OpenAI(
    api_key="dummy",  # 本地服务不需要真实 key
    base_url="http://localhost:8000/v1"
)

# 简单对话
response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "你好"}
    ],
    max_tokens=100
)
print(response.choices[0].message.content)

# 流式输出
stream = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "数到10"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### curl

```bash
# 非流式
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 50
  }'

# 流式
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "数到5"}],
    "stream": true
  }'
```

## 📊 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/chat/completions` | POST | 聊天接口（OpenAI 兼容） |
| `/generate` | POST | 文本生成接口（简单版） |
| `/docs` | GET | API 文档（Swagger UI） |

## 🐳 Docker 部署

### CPU 版本（本地测试）

```bash
# 一键部署
./deploy-cpu.sh

# 或手动部署
docker-compose -f docker-compose.cpu.yml up -d

# 查看日志
docker logs -f qwen-llm-service-cpu

# 停止服务
docker-compose -f docker-compose.cpu.yml down
```

### GPU 版本（生产环境）

```bash
docker-compose up -d
```

## ⚙️ 配置

编辑 `config.py`:

```python
# 模型配置
MODEL_PATH = "/path/to/your/model"
MODEL_NAME = "your-model-name"

# 服务配置
SERVICE_HOST = "0.0.0.0"
SERVICE_PORT = 8000
```

或使用环境变量：

```bash
export MODEL_PATH="/path/to/model"
export MODEL_NAME="qwen"
export SERVICE_PORT=8000
```

## 🧪 测试

```bash
# Docker 测试
./test-docker.sh

# 本地测试
python test_openai_compatibility.py

# 简单测试
curl http://localhost:8000/health
```

## 📈 性能

### CPU 模式（本地测试）
- 启动时间：1-2 分钟
- 推理速度：10-30 秒/请求
- 适用场景：开发测试

### GPU 模式（生产环境）
- 启动时间：30-60 秒
- 推理速度：1-3 秒/请求
- 适用场景：生产部署

## 🔄 从 OpenAI 迁移

**零代码改动！** 只需修改两行配置：

```python
# 原来
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 改成
client = openai.OpenAI(
    api_key="dummy",
    base_url="http://your-server:8000/v1"
)
```

其他代码完全不用改！详见 [OPENAI_COMPATIBILITY.md](OPENAI_COMPATIBILITY.md)

## 🛠️ 开发

```bash
# 克隆项目
git clone <your-repo>
cd llm_service

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements-cpu.txt

# 运行服务
python llm_service_cpu.py
```

## 📁 项目结构

```
llm_service/
├── llm_service_cpu.py          # CPU 版本服务（Transformers）
├── llm_service.py              # GPU 版本服务（vLLM）
├── config.py                   # 配置文件
├── requirements-cpu.txt        # CPU 版本依赖
├── requirements.txt            # GPU 版本依赖
├── Dockerfile.cpu              # CPU Docker 镜像
├── Dockerfile                  # GPU Docker 镜像
├── docker-compose.cpu.yml      # CPU Docker Compose
├── docker-compose.yml          # GPU Docker Compose
├── deploy-cpu.sh ⭐           # 一键部署脚本
├── test-docker.sh ⭐          # Docker 测试脚本
├── test_openai_compatibility.py # OpenAI 兼容性测试
└── *.md                        # 文档
```

## ❓ 常见问题

### Q: 服务启动很慢？
A: 正常现象。模型加载需要 1-2 分钟（CPU）或 30-60 秒（GPU）。

### Q: CPU 模式推理很慢？
A: CPU 推理本身就慢，仅用于测试。生产环境请使用 GPU。

### Q: 如何更换模型？
A: 修改 `config.py` 中的 `MODEL_PATH` 和 `MODEL_NAME`。

### Q: 支持哪些模型？
A: 所有 Hugging Face/ModelScope 上的 Causal LM 模型（如 Qwen、LLaMA 等）。

### Q: 如何添加 API Key 认证？
A: 在 FastAPI 中添加中间件，验证请求头中的 API Key。

## 📄 许可证

MIT

## 🙏 致谢

- [Qwen](https://github.com/QwenLM/Qwen) - 基座模型
- [vLLM](https://github.com/vllm-project/vllm) - GPU 推理引擎
- [Transformers](https://github.com/huggingface/transformers) - CPU 推理支持
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
