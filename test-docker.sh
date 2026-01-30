#!/bin/bash
# Docker 测试脚本 - 测试部署的容器化服务

set -e

echo "=========================================="
echo "🧪 LLM Service Docker 测试"
echo "=========================================="

# 检查服务是否运行
if ! docker ps | grep -q qwen-llm-service-cpu; then
    echo "❌ 服务未运行"
    echo "请先运行: ./deploy-cpu.sh"
    exit 1
fi

echo ""
echo "✅ 服务正在运行"
echo ""

# 测试1: 健康检查
echo "测试 1/5: 健康检查..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  ✅ 健康检查通过"
    echo "  响应: $HEALTH"
else
    echo "  ❌ 健康检查失败"
    exit 1
fi

# 测试2: 非流式对话
echo ""
echo "测试 2/5: 非流式对话..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen",
        "messages": [
            {"role": "system", "content": "你是一个简洁的助手，回答要简短。"},
            {"role": "user", "content": "1+1等于几？"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }')

if echo "$RESPONSE" | grep -q "content"; then
    echo "  ✅ 非流式对话成功"
    CONTENT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "解析失败")
    echo "  模型回答: $CONTENT"
    
    # 检查 token 统计
    if echo "$RESPONSE" | grep -q "usage"; then
        USAGE=$(echo "$RESPONSE" | python3 -c "import sys, json; u=json.load(sys.stdin)['usage']; print(f\"输入={u['prompt_tokens']}, 输出={u['completion_tokens']}, 总计={u['total_tokens']}\")" 2>/dev/null || echo "解析失败")
        echo "  Token 统计: $USAGE"
    fi
else
    echo "  ❌ 非流式对话失败"
    echo "  响应: $RESPONSE"
    exit 1
fi

# 测试3: 多轮对话（带历史）
echo ""
echo "测试 3/5: 多轮对话（带历史）..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen",
        "messages": [
            {"role": "user", "content": "我叫小明"},
            {"role": "assistant", "content": "你好，小明！"},
            {"role": "user", "content": "我叫什么？"}
        ],
        "max_tokens": 30
    }')

if echo "$RESPONSE" | grep -q "content"; then
    echo "  ✅ 多轮对话成功"
    CONTENT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "解析失败")
    echo "  模型回答: $CONTENT"
else
    echo "  ❌ 多轮对话失败"
    exit 1
fi

# 测试4: 流式输出
echo ""
echo "测试 4/5: 流式输出..."
STREAM_RESPONSE=$(curl -s -N -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "qwen",
        "messages": [{"role": "user", "content": "数到5"}],
        "max_tokens": 50,
        "stream": true
    }')

if echo "$STREAM_RESPONSE" | grep -q "data:"; then
    echo "  ✅ 流式输出成功"
    echo "  (收到流式数据块)"
else
    echo "  ❌ 流式输出失败"
    exit 1
fi

# 测试5: OpenAI SDK 兼容性（如果已安装）
echo ""
echo "测试 5/5: OpenAI SDK 兼容性..."
if command -v python3 &> /dev/null && python3 -c "import openai" 2>/dev/null; then
    python3 << 'EOF'
import openai
import sys

try:
    client = openai.OpenAI(
        api_key="dummy",
        base_url="http://localhost:8000/v1"
    )
    
    response = client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": "Say OK"}],
        max_tokens=10
    )
    
    print(f"  ✅ OpenAI SDK 测试成功")
    print(f"  响应: {response.choices[0].message.content}")
except Exception as e:
    print(f"  ❌ OpenAI SDK 测试失败: {e}")
    sys.exit(1)
EOF
else
    echo "  ⚠️  跳过 (未安装 openai 包)"
    echo "     安装方法: pip install openai"
fi

# 查看容器资源使用
echo ""
echo "=========================================="
echo "📊 容器资源使用情况:"
echo "=========================================="
docker stats qwen-llm-service-cpu --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "=========================================="
echo "🎉 所有测试通过！"
echo "=========================================="
echo ""
echo "📝 日志查看:"
echo "  docker logs -f qwen-llm-service-cpu"
echo ""
echo "🛑 停止服务:"
echo "  docker-compose -f docker-compose.cpu.yml down"
echo ""
