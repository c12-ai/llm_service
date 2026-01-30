# OpenAI API 兼容性说明

## ✅ 完全兼容

你的 LLM Service 现在**完全兼容 OpenAI API**，客户端无需修改代码即可切换！

## 使用方式

### 方式1：使用 OpenAI Python SDK（推荐）

```python
import openai

# 只需修改这两行配置
client = openai.OpenAI(
    api_key="any-dummy-key",  # 可以填任意值
    base_url="http://your-server:8000/v1"  # 改成你的服务地址
)

# 其他代码完全不变
response = client.chat.completions.create(
    model="gpt-4",  # model 参数会被忽略，服务端使用实际加载的模型
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    temperature=0.7,
    max_tokens=100,
    stream=True  # 支持流式输出
)
```

### 方式2：使用环境变量

```bash
# 设置环境变量
export OPENAI_API_KEY="any-dummy-key"
export OPENAI_BASE_URL="http://your-server:8000/v1"
```

```python
import openai

# 会自动读取环境变量
client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### 方式3：使用 curl（测试）

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

## 支持的参数

### ✅ 已支持

- `model`: 模型名称（可选，服务端只有一个模型）
- `messages`: 对话历史（必填）
- `max_tokens`: 最大生成 token 数
- `temperature`: 采样温度
- `top_p`: nucleus 采样
- `stream`: 流式输出（支持！）
- `stop`: 停止词（字符串或列表）
- `n`: 生成数量（目前仅支持 1）
- `user`: 用户标识

### ⚠️ 接受但忽略

- `presence_penalty`: 存在惩罚（transformers 不支持）
- `frequency_penalty`: 频率惩罚（transformers 不支持）

### 响应格式

完全符合 OpenAI 标准：

```json
{
  "id": "chatcmpl-abc12345",
  "object": "chat.completion",
  "created": 1706524800,
  "model": "qwen",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "生成的内容"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  }
}
```

## 迁移步骤

### 对于客户端（调用方）

1. **安装依赖**（如果还没有）：
   ```bash
   pip install openai
   ```

2. **修改配置**（仅需改2行）：
   ```python
   # 原来
   client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   
   # 改成
   client = openai.OpenAI(
       api_key="dummy",  # 随便填
       base_url="http://your-llm-service:8000/v1"  # 你的服务地址
   )
   ```

3. **其他代码不用改**：
   - `client.chat.completions.create(...)` 完全一样
   - `stream=True` 流式输出可以继续用
   - 错误处理逻辑不用改

### 对于服务端（你的项目）

1. **安装依赖**：
   ```bash
   pip install openai  # 用于测试
   ```

2. **启动服务**：
   ```bash
   python llm_service_cpu.py
   ```

3. **测试兼容性**：
   ```bash
   python test_openai_compatibility.py
   ```

## 注意事项

1. **模型参数会被忽略**：客户端传的 `model` 参数（如 `gpt-4-mini`）会被忽略，服务端使用实际加载的模型（config.py 中配置的）。

2. **API Key 可以随便填**：本地服务不需要验证，但客户端 SDK 要求必须传这个参数，所以填任意值即可。

3. **历史消息由客户端管理**：服务端不存储对话历史，客户端每次请求需要带上完整的 `messages`。

4. **Token 使用会增加**：对话轮数越多，输入 token 越多，响应会越慢。

5. **流式输出推荐用于生产环境**：提升用户体验，减少首字延迟。

## 性能优化建议

如果对话历史很长（超过 2000 tokens），建议：

1. 只保留最近 N 轮对话
2. 或者使用摘要压缩历史
3. 或者限制 `max_tokens` 避免超出上下文长度

## 测试示例

运行测试脚本验证兼容性：

```bash
# 先启动服务
python llm_service_cpu.py

# 另一个终端运行测试
python test_openai_compatibility.py
```

如果看到 "✅ 所有测试完成"，说明完全兼容！

## 常见问题

**Q: 客户端报错 "Invalid API key"？**  
A: 检查 `base_url` 是否正确，应该是 `http://host:port/v1`，注意最后有 `/v1`。

**Q: 流式输出不工作？**  
A: 确保请求中传了 `stream=True`。

**Q: Token 统计不准确？**  
A: `usage` 中的 token 数是估算值，与 OpenAI 可能略有差异，但不影响使用。

**Q: 能否同时兼容 OpenAI 和自建服务？**  
A: 可以！在客户端用配置开关决定使用哪个 `base_url`。
