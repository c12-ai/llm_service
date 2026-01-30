# 🚀 Docker 本地测试 - 快速开始

## 一键部署（推荐）

```bash
# 1. 确保已下载模型
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"

# 2. 一键部署
./deploy-cpu.sh

# 3. 运行测试
./test-docker.sh
```

就这么简单！🎉

## 详细步骤

### 前置准备

1. **安装 Docker**
   - macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: `curl -fsSL https://get.docker.com | sh`

2. **下载模型**（如果还没有）
   ```bash
   pip install modelscope
   python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"
   ```

### 部署服务

```bash
# 方式1: 使用一键部署脚本（推荐）⭐
./deploy-cpu.sh

# 方式2: 手动部署
docker-compose -f docker-compose.cpu.yml up -d

# 等待服务启动（1-2分钟）
docker logs -f qwen-llm-service-cpu
```

### 测试 API

```bash
# 运行完整测试套件 ⭐
./test-docker.sh

# 或手动测试
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","messages":[{"role":"user","content":"你好"}],"max_tokens":50}'
```

### 查看文档

```bash
# 快速参考
./docker-quick-ref.sh

# 详细部署指南
cat DOCKER_DEPLOYMENT.md

# OpenAI API 兼容性说明
cat OPENAI_COMPATIBILITY.md
```

## 常用命令

| 操作 | 命令 |
|------|------|
| 部署服务 | `./deploy-cpu.sh` |
| 运行测试 | `./test-docker.sh` |
| 查看日志 | `docker logs -f qwen-llm-service-cpu` |
| 停止服务 | `docker-compose -f docker-compose.cpu.yml down` |
| 重启服务 | `docker-compose -f docker-compose.cpu.yml restart` |
| 查看快速参考 | `./docker-quick-ref.sh` |

## 访问地址

- **API 地址**: http://localhost:8000
- **健康检查**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/docs
- **交互式文档**: http://localhost:8000/redoc

## 使用 OpenAI SDK

```python
import openai

# 只需修改这两行
client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

# 其他代码完全一样
response = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=50
)

print(response.choices[0].message.content)
```

## 性能说明

⚠️ **CPU 模式性能**：
- 启动时间：1-2 分钟（模型加载）
- 推理速度：每个请求约 10-30 秒
- 仅用于本地测试，**不建议生产使用**
- 生产环境请使用 GPU 版本

## 故障排查

### 服务启动失败？

```bash
# 查看日志
docker logs qwen-llm-service-cpu

# 常见问题：
# 1. 模型路径不存在 → 检查 ~/.cache/modelscope/hub/models/Qwen/Qwen3-4B
# 2. 端口被占用 → 修改 docker-compose.cpu.yml 中的端口
# 3. 内存不足 → 确保至少有 8GB 可用内存
```

### 如何停止服务？

```bash
docker-compose -f docker-compose.cpu.yml down
```

### 如何更换模型？

编辑 `docker-compose.cpu.yml`:
```yaml
environment:
  - MODEL_PATH=/models/YourModel
  - MODEL_NAME=YourModel
```

然后重启：
```bash
docker-compose -f docker-compose.cpu.yml up -d --force-recreate
```

## 文件清单

```
📁 Docker 部署文件
├── Dockerfile.cpu              # CPU 版本镜像定义
├── docker-compose.cpu.yml      # 容器编排配置
├── .dockerignore               # Docker 忽略规则
├── deploy-cpu.sh ⭐            # 一键部署脚本
├── test-docker.sh ⭐           # 测试脚本
├── docker-quick-ref.sh         # 快速参考
├── DOCKER_DEPLOYMENT.md        # 详细部署指南
└── DOCKER_QUICKSTART.md        # 本文档
```

## 下一步

✅ 完成本地测试后，可以：

1. **切换到 GPU 版本**（生产环境）
   ```bash
   docker-compose up -d
   ```

2. **部署到云端**
   - 阿里云 / 腾讯云 / AWS
   - 使用 Kubernetes

3. **添加负载均衡**
   - 多副本部署
   - Nginx 反向代理

4. **添加监控**
   - Prometheus + Grafana
   - 日志聚合

## 获取帮助

- 📖 **详细文档**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- 🔧 **快速参考**: `./docker-quick-ref.sh`
- 🐛 **查看日志**: `docker logs -f qwen-llm-service-cpu`
- 🧪 **运行测试**: `./test-docker.sh`

---

**提示**: 如果这是你第一次使用，建议先运行 `./deploy-cpu.sh`，它会自动完成所有步骤并运行测试！
