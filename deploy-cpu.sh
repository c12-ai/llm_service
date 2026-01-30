#!/bin/bash
# Docker 部署脚本 - CPU版本（本地测试）

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 LLM Service Docker 部署 (CPU版本)"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 设置 Docker Compose 命令
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 检查模型是否存在
# MODEL_PATH="${HOME}/.cache/modelscope/hub/models/Qwen/Qwen3-4B"
# if [ ! -d "$MODEL_PATH" ]; then
#     echo "⚠️  警告: 模型目录不存在: $MODEL_PATH"
#     echo "请先运行以下命令下载模型:"
#     echo "  python -c \"from modelscope import snapshot_download; snapshot_download('Qwen/Qwen3-4B')\""
#     read -p "是否继续部署? (y/n) " -n 1 -r
#     echo
#     if [[ ! $REPLY =~ ^[Yy]$ ]]; then
#         exit 1
#     fi
# fi

echo ""
echo "📦 步骤 1/4: 构建 Docker 镜像..."
$DOCKER_COMPOSE -f docker-compose.cpu.yml build

echo ""
echo "🚀 步骤 2/4: 启动服务..."
$DOCKER_COMPOSE -f docker-compose.cpu.yml up -d

echo ""
echo "⏳ 步骤 3/4: 等待服务启动（模型加载中，可能需要1-2分钟）..."
echo "   提示: 可以用 'docker logs -f qwen-llm-service-cpu' 查看实时日志"

# 等待服务健康
MAX_WAIT=180  # 最多等待3分钟
WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 服务启动成功！"
        break
    fi
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    echo -n "."
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠️  服务启动超时，请检查日志:"
    echo "  docker logs qwen-llm-service-cpu"
    exit 1
fi

echo ""
echo "🧪 步骤 4/4: 测试 API..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 20
    }')

if echo "$RESPONSE" | grep -q "content"; then
    echo "✅ API 测试成功！"
    echo ""
    echo "=========================================="
    echo "🎉 部署完成！"
    echo "=========================================="
    echo ""
    echo "📝 服务信息:"
    echo "  - 容器名称: qwen-llm-service-cpu"
    echo "  - 访问地址: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo ""
    echo "🔧 常用命令:"
    echo "  查看日志:   docker logs -f qwen-llm-service-cpu"
    echo "  停止服务:   $DOCKER_COMPOSE -f docker-compose.cpu.yml down"
    echo "  重启服务:   $DOCKER_COMPOSE -f docker-compose.cpu.yml restart"
    echo "  查看状态:   docker ps | grep qwen"
    echo ""
    echo "📖 测试示例:"
    echo "  curl -X POST http://localhost:8000/v1/chat/completions \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"model\":\"qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}]}'"
    echo ""
else
    echo "❌ API 测试失败"
    echo "响应: $RESPONSE"
    echo ""
    echo "请检查日志:"
    echo "  docker logs qwen-llm-service-cpu"
    exit 1
fi
