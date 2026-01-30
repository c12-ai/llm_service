# Docker 部署指南 - CPU版本（本地测试）

## 📋 前置要求

### 1. 系统要求
- **操作系统**: macOS / Linux / Windows (WSL2)
- **内存**: 至少 8GB RAM（推荐 16GB+）
- **磁盘**: 至少 10GB 可用空间（模型 + 镜像）
- **CPU**: 4核心以上（推荐）

### 2. 软件依赖
- Docker Engine 20.10+
- Docker Compose v2.0+ 或 docker-compose 1.29+

### 3. 验证安装
```bash
# 检查 Docker
docker --version
docker ps

# 检查 Docker Compose
docker compose version
# 或
docker-compose --version
```

## 🚀 快速开始（一键部署）

### 步骤 1: 下载模型（如果还没有）

```bash
# 安装 modelscope
pip install modelscope

# 下载 Qwen3-4B 模型（约 8GB）
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')"
```

模型会下载到：`~/.cache/modelscope/hub/models/Qwen/Qwen3-4B`

### 步骤 2: 一键部署

```bash
# 给部署脚本执行权限
chmod +x deploy-cpu.sh

# 运行部署脚本
./deploy-cpu.sh
```

脚本会自动完成：
1. ✅ 构建 Docker 镜像
2. ✅ 启动容器服务
3. ✅ 等待模型加载
4. ✅ 健康检查
5. ✅ API 测试

看到 "🎉 部署完成！" 说明服务已就绪。

### 步骤 3: 运行测试

```bash
# 给测试脚本执行权限
chmod +x test-docker.sh

# 运行完整测试
./test-docker.sh
```

## 📖 手动部署（逐步操作）

如果你想了解每一步的细节：

### 1. 构建镜像

```bash
docker build -f Dockerfile.cpu -t llm-service-cpu:latest .
```

### 2. 启动容器

```bash
docker-compose -f docker-compose.cpu.yml up -d
```

或使用 docker run（不推荐，配置复杂）：

```bash
docker run -d \
  --name qwen-llm-service-cpu \
  -p 8000:8000 \
  -v ~/.cache/modelscope/hub/models/Qwen:/models:ro \
  -e MODEL_PATH=/models/Qwen3-4B \
  -e MODEL_NAME=Qwen3-4B \
  --cpus=4 \
  --memory=16g \
  llm-service-cpu:latest
```

### 3. 查看日志

```bash
# 实时日志
docker logs -f qwen-llm-service-cpu

# 最近100行
docker logs --tail 100 qwen-llm-service-cpu
```

### 4. 检查健康状态

```bash
curl http://localhost:8000/health
```

预期输出：
```json
{
  "status": "healthy",
  "model": "/models/Qwen3-4B",
  "device": "cpu",
  "warning": "CPU模式运行，速度较慢"
}
```

## 🧪 测试 API

### 方式1: 使用 curl

```bash
# 简单对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 50
  }'
```

### 方式2: 使用 Python OpenAI SDK

```python
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "user", "content": "你好"}
    ],
    max_tokens=50
)

print(response.choices[0].message.content)
```

### 方式3: 流式输出

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "数到10"}],
    "max_tokens": 100,
    "stream": true
  }'
```

## 🔧 常用命令

### 容器管理

```bash
# 查看运行状态
docker ps | grep qwen

# 查看资源使用
docker stats qwen-llm-service-cpu

# 停止服务
docker-compose -f docker-compose.cpu.yml down

# 重启服务
docker-compose -f docker-compose.cpu.yml restart

# 重新构建并启动
docker-compose -f docker-compose.cpu.yml up -d --build
```

### 日志和调试

```bash
# 实时日志
docker logs -f qwen-llm-service-cpu

# 进入容器
docker exec -it qwen-llm-service-cpu /bin/bash

# 查看容器详情
docker inspect qwen-llm-service-cpu
```

### 清理

```bash
# 停止并删除容器
docker-compose -f docker-compose.cpu.yml down

# 删除镜像
docker rmi llm-service-cpu:latest

# 清理未使用的资源
docker system prune -a
```

## ⚙️ 配置调整

### 修改模型路径

编辑 `docker-compose.cpu.yml`:

```yaml
volumes:
  - /your/custom/path:/models:ro  # 修改这里

environment:
  - MODEL_PATH=/models/YourModel  # 修改这里
  - MODEL_NAME=YourModel          # 修改这里
```

### 调整资源限制

编辑 `docker-compose.cpu.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '8'      # 增加 CPU 核心数
      memory: 32G    # 增加内存
```

### 修改端口

编辑 `docker-compose.cpu.yml`:

```yaml
ports:
  - "9000:8000"  # 宿主机端口:容器端口
```

## 🐛 故障排查

### 问题1: 容器启动失败

**症状**: `docker ps` 看不到容器

**解决**:
```bash
# 查看启动日志
docker logs qwen-llm-service-cpu

# 常见原因:
# 1. 模型路径不存在
# 2. 端口被占用
# 3. 内存不足
```

### 问题2: 模型加载失败

**症状**: 日志显示 "模型加载失败"

**解决**:
```bash
# 检查模型目录挂载
docker exec qwen-llm-service-cpu ls -la /models

# 确保模型文件存在
ls -la ~/.cache/modelscope/hub/models/Qwen/Qwen3-4B
```

### 问题3: 服务响应很慢

**症状**: API 响应时间 > 30秒

**原因**: CPU 推理本身很慢（正常现象）

**优化建议**:
1. 使用更小的模型
2. 减少 `max_tokens`
3. 增加 CPU 核心限制
4. 使用 GPU 版本（生产环境）

### 问题4: 健康检查失败

**症状**: 容器不断重启

**解决**:
```bash
# 增加启动等待时间
# 编辑 docker-compose.cpu.yml
healthcheck:
  start_period: 300s  # 从 120s 改为 300s
```

### 问题5: 端口冲突

**症状**: "port is already allocated"

**解决**:
```bash
# 查看占用端口的进程
lsof -i :8000

# 方式1: 停止占用端口的进程
kill -9 <PID>

# 方式2: 使用其他端口（修改 docker-compose.cpu.yml）
ports:
  - "8001:8000"
```

## 📊 性能基准

在 MacBook Pro (M1, 16GB) 上的测试结果：

| 场景 | 输入 Tokens | 输出 Tokens | 响应时间 |
|------|------------|-------------|----------|
| 简单问答 | 20 | 50 | ~15秒 |
| 多轮对话 | 100 | 50 | ~25秒 |
| 长文本生成 | 50 | 200 | ~60秒 |

**注意**: CPU 推理仅用于本地测试，生产环境请使用 GPU 版本。

## 🔐 安全建议

1. **生产环境**:
   - 添加 API Key 认证
   - 使用反向代理（Nginx）
   - 启用 HTTPS
   - 配置防火墙

2. **容器安全**:
   - 不要以 root 用户运行
   - 限制容器资源
   - 定期更新基础镜像

3. **模型保护**:
   - 使用只读挂载 (`:ro`)
   - 避免将模型打包进镜像
   - 定期备份模型文件

## 📚 下一步

- ✅ **已完成**: CPU 版本本地测试
- 🔄 **可选**: 切换到 GPU 版本（使用 `Dockerfile` 和 `docker-compose.yml`）
- 🚀 **生产部署**: 使用 Kubernetes / Docker Swarm
- 📈 **监控**: 添加 Prometheus + Grafana
- 🔄 **负载均衡**: 部署多个副本 + Nginx

## 🆘 获取帮助

- **查看日志**: `docker logs -f qwen-llm-service-cpu`
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **运行测试**: `./test-docker.sh`

## 附录: 文件清单

```
llm_service/
├── Dockerfile.cpu              # CPU版本 Dockerfile
├── docker-compose.cpu.yml      # CPU版本 Compose 配置
├── deploy-cpu.sh               # 一键部署脚本 ⭐
├── test-docker.sh              # 测试脚本 ⭐
├── .dockerignore               # Docker 忽略文件
├── llm_service_cpu.py          # 服务代码
├── config.py                   # 配置文件
├── requirements-cpu.txt        # Python 依赖
└── DOCKER_DEPLOYMENT.md        # 本文档
```

**关键文件**:
- ⭐ `deploy-cpu.sh`: 一键部署
- ⭐ `test-docker.sh`: 完整测试
- 📝 `Dockerfile.cpu`: 镜像构建
- 📝 `docker-compose.cpu.yml`: 容器编排
