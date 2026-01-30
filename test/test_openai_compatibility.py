"""
测试 OpenAI API 兼容性
可以使用标准的 OpenAI Python SDK 调用
"""
import openai
import time

# 配置指向你的本地服务
client = openai.OpenAI(
    api_key="dummy-key",  # 本地服务不需要真实的 API key
    base_url="http://localhost:8000/v1"  # 指向你的本地服务
)

print("=" * 60)
print("测试 1: 非流式对话")
print("=" * 60)

response = client.chat.completions.create(
    model="qwen",  # 可以传任意值，服务端会使用实际加载的模型
    messages=[
        {"role": "system", "content": "你是一个有用的助手。"},
        {"role": "user", "content": "用一句话介绍Python"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(f"Response ID: {response.id}")
print(f"Model: {response.model}")
print(f"Created: {response.created}")
print(f"Content: {response.choices[0].message.content}")
print(f"Finish Reason: {response.choices[0].finish_reason}")
print(f"Usage: {response.usage}")

print("\n" + "=" * 60)
print("测试 2: 流式对话")
print("=" * 60)

stream = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "user", "content": "数到10"}
    ],
    max_tokens=100,
    temperature=0.7,
    stream=True  # 启用流式输出
)

print("Streaming output: ", end="", flush=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\n")

print("\n" + "=" * 60)
print("测试 3: 多轮对话（带历史）")
print("=" * 60)

response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "system", "content": "你是一个简洁的助手。"},
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "你好，小明！"},
        {"role": "user", "content": "我叫什么？"}
    ],
    max_tokens=50
)

print(f"Content: {response.choices[0].message.content}")
print(f"Token Usage: Prompt={response.usage.prompt_tokens}, "
      f"Completion={response.usage.completion_tokens}, "
      f"Total={response.usage.total_tokens}")

print("\n✅ 所有测试完成！你的服务完全兼容 OpenAI API")
print("客户端可以无缝切换，只需修改 base_url 即可")
