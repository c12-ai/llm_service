"""
测试客户端 - 用于测试LLM服务接口
"""
import requests
import json

# 服务地址
BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_generate():
    """测试文本生成接口"""
    print("=" * 60)
    print("测试文本生成接口...")
    
    data = {
        "prompt": "请用一句话介绍人工智能：",
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"生成文本: {result['text']}")
    else:
        print(f"错误: {response.text}")
    print()


def test_chat():
    """测试聊天接口"""
    print("=" * 60)
    print("测试聊天接口...")
    
    data = {
        "messages": [
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": "什么是机器学习？请简短回答。"}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"助手回复: {result['choices'][0]['message']['content']}")
    else:
        print(f"错误: {response.text}")
    print()


def main():
    """运行所有测试"""
    print("\n🧪 开始测试 LLM 服务\n")
    
    try:
        # 1. 健康检查
        test_health()
        
        # 2. 文本生成
        test_generate()
        
        # 3. 聊天接口
        test_chat()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务已启动：")
        print("   python llm_service_cpu.py")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    main()
