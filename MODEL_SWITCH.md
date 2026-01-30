# 🔄 模型快速切换指南

## 概述

现在支持通过 `.env` 文件快速切换模型，**无需修改代码**！

## 🚀 快速切换（3步搞定）

### 步骤 1: 创建 .env 配置文件

```bash
# 复制模板文件
cp .env.example .env
```

### 步骤 2: 编辑 .env 文件

打开 `.env` 文件，取消注释你想用的模型：

```bash
# 例如：切换到 Qwen2.5-7B-Instruct
MODEL_PATH=/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct
MODEL_NAME=Qwen2.5-7B-Instruct
```

### 步骤 3: 重启服务

```bash
# Docker 部署
docker-compose -f docker-compose.cpu.yml restart

# 或本地运行
python llm_service_cpu.py
```

## 📋 支持的模型

### Qwen 系列（推荐）

| 模型 | 大小 | 内存需求 | 适用场景 | modelscope 下载命令 |
|------|------|----------|----------|---------------------|
| **Qwen3-4B** | ~8GB | 8GB+ | 快速测试 | `snapshot_download('Qwen/Qwen3-4B')` |
| **Qwen2.5-7B-Instruct** | ~14GB | 16GB+ | 推荐，平衡性能 | `snapshot_download('Qwen/Qwen2.5-7B-Instruct')` |
| **Qwen2.5-14B-Instruct** | ~28GB | 32GB+ | 更强性能 | `snapshot_download('Qwen/Qwen2.5-14B-Instruct')` |
| **Qwen2.5-32B-Instruct** | ~64GB | 64GB+ | 旗舰模型 | `snapshot_download('Qwen/Qwen2.5-32B-Instruct')` |

## 📝 详细步骤

### 方式 1: Docker 部署（推荐）

#### 1. 下载新模型

```bash
# 安装 modelscope（如果还没有）
pip install modelscope

# 下载模型（例如 Qwen2.5-7B-Instruct）
python -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct')"
```

模型会下载到：`~/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct`

#### 2. 修改 .env 配置

创建或编辑 `.env` 文件：

```bash
# 复制模板（首次）
cp .env.example .env

# 编辑配置
nano .env  # 或使用其他编辑器
```

修改以下内容：

```bash
MODEL_PATH=/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct
MODEL_NAME=Qwen2.5-7B-Instruct
```

#### 3. 重启 Docker 服务

```bash
# 方式 1: 重启容器（快速，推荐）
docker-compose -f docker-compose.cpu.yml restart

# 方式 2: 重新创建容器（更彻底）
docker-compose -f docker-compose.cpu.yml down
docker-compose -f docker-compose.cpu.yml up -d

# 方式 3: 使用一键部署脚本
./deploy-cpu.sh
```

#### 4. 验证切换成功

```bash
# 查看健康检查
curl http://localhost:8000/health

# 预期输出应包含新模型名称
# {
#   "status": "healthy",
#   "model": "/models/Qwen2.5-7B-Instruct",
#   ...
# }

# 或查看日志
docker logs qwen-llm-service-cpu | grep "正在加载模型"
```

### 方式 2: 本地运行

#### 1. 下载模型（同上）

#### 2. 设置环境变量

```bash
# 临时设置（当前终端有效）
export MODEL_PATH="/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct"
export MODEL_NAME="Qwen2.5-7B-Instruct"

# 或永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export MODEL_PATH="/Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct"' >> ~/.zshrc
echo 'export MODEL_NAME="Qwen2.5-7B-Instruct"' >> ~/.zshrc
```

#### 3. 启动服务

```bash
python llm_service_cpu.py
```

## 🔧 高级配置

### 使用自定义模型路径

如果你的模型不在 modelscope 缓存目录：

**编辑 .env**:
```bash
# 自定义模型路径
MODEL_PATH=/your/custom/path/to/model
MODEL_NAME=your-custom-model

# Docker 还需要修改挂载路径
HOST_MODEL_DIR=/your/custom/path
CONTAINER_MODEL_DIR=/models

# 确保 MODEL_PATH 以 CONTAINER_MODEL_DIR 开头
# 例如：MODEL_PATH=/models/your-model
```

**修改挂载映射**（Docker）:
```yaml
# docker-compose.cpu.yml 会自动读取 .env 中的 HOST_MODEL_DIR
volumes:
  - ${HOST_MODEL_DIR}:${CONTAINER_MODEL_DIR}:ro
```

### 调整资源限制

编辑 `.env`:

```bash
# 给大模型更多资源
CPU_LIMIT=8
MEMORY_LIMIT=32G
CPU_RESERVATION=4
MEMORY_RESERVATION=16G
```

### 修改服务端口

编辑 `.env`:

```bash
SERVICE_PORT=9000
```

## 📊 模型性能对比（CPU 模式）

| 模型 | 启动时间 | 单次推理 | 内存占用 | 质量评分 |
|------|---------|---------|---------|---------|
| Qwen3-4B | ~60s | ~15s | ~6GB | ⭐⭐⭐ |
| Qwen2.5-7B-Instruct | ~90s | ~25s | ~12GB | ⭐⭐⭐⭐ |
| Qwen2.5-14B-Instruct | ~120s | ~45s | ~24GB | ⭐⭐⭐⭐⭐ |

**注意**: CPU 模式仅用于测试，生产环境请使用 GPU。

## 🐛 常见问题

### Q: 切换模型后启动失败？

**A**: 检查以下几点：

1. **模型是否下载完整**
   ```bash
   ls -lh ~/.cache/modelscope/hub/models/Qwen/你的模型名/
   # 应该有 config.json, model files 等
   ```

2. **路径是否正确**
   ```bash
   # 查看环境变量
   echo $MODEL_PATH
   
   # Docker 中检查
   docker exec qwen-llm-service-cpu ls -la /models/
   ```

3. **内存是否足够**
   ```bash
   # 查看可用内存
   free -h  # Linux
   vm_stat  # macOS
   ```

### Q: Docker 挂载路径不对？

**A**: 确保 `HOST_MODEL_DIR` 和 `MODEL_PATH` 的映射关系正确：

```bash
# .env 中
HOST_MODEL_DIR=/Users/tengpi/.cache/modelscope/hub/models/Qwen
CONTAINER_MODEL_DIR=/models
MODEL_PATH=/models/Qwen2.5-7B-Instruct  # 注意：/models 是容器内路径

# 映射关系：
# 宿主机: /Users/tengpi/.cache/modelscope/hub/models/Qwen/Qwen2.5-7B-Instruct
# 容器内: /models/Qwen2.5-7B-Instruct
```

### Q: 如何验证模型已切换？

**A**: 多种方式验证：

```bash
# 1. 健康检查 API
curl http://localhost:8000/health | jq .model

# 2. 查看日志
docker logs qwen-llm-service-cpu 2>&1 | grep "正在加载模型"

# 3. 测试对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"test","messages":[{"role":"user","content":"你是哪个模型？"}]}'
```

### Q: 可以同时运行多个模型吗？

**A**: 可以，但需要修改端口和容器名：

```bash
# 复制配置文件
cp .env .env.model1
cp .env .env.model2

# 编辑不同的模型配置
# .env.model1: MODEL_PATH=.../Qwen3-4B, SERVICE_PORT=8001
# .env.model2: MODEL_PATH=.../Qwen2.5-7B, SERVICE_PORT=8002

# 使用不同的 env 文件启动
docker-compose --env-file .env.model1 -f docker-compose.cpu.yml -p model1 up -d
docker-compose --env-file .env.model2 -f docker-compose.cpu.yml -p model2 up -d
```

## 📚 相关文档

- [.env.example](.env.example) - 环境变量模板
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Docker 部署指南
- [README.md](README.md) - 项目总览

## 🎯 总结

切换模型只需 3 步：

1. ✅ 下载新模型 → `snapshot_download('Qwen/模型名')`
2. ✅ 修改 `.env` → 改 `MODEL_PATH` 和 `MODEL_NAME`
3. ✅ 重启服务 → `docker-compose restart`

无需修改任何代码！🎉
