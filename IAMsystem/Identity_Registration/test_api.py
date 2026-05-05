import requests
import json

BASE_URL = "http://localhost:9000/IAMsystem"

def test_user_registration():
    print("=== 测试用户注册 ===")
    data = {
        "Agent_name": "测试用户2026",
        "subtype": "user",
        "scope": {"doc": ["read", "write"], "online": ["web_search"]},
        "ip": "192.168.1.100"
    }
    response = requests.post(f"{BASE_URL}/identity/register/user", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    return response.json()

def test_bot_registration():
    print("=== 测试机器注册 ===")
    data = {
        "Bot_name": "测试机器人2026",
        "scope": {"online": ["web_search", "fetch_content"], "iam": ["verify_token"]},
        "sub_scope": {
            "user": {"online": ["web_search", "fetch_content"]},
            "visitor": {"online": ["web_search"]}
        },
        "ip": "127.0.0.1",
        "api_endpoint": "http://localhost:8002/api"
    }
    response = requests.post(f"{BASE_URL}/identity/register/bot", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    return response.json()

def test_identity_verify(user_data):
    print("=== 测试身份校验 ===")
    if user_data and "data" in user_data:
        data = {
            "agent_id": user_data["data"]["agent_id"],
            "agent_secret": user_data["data"]["agent_secret"]
        }
        response = requests.post(f"{BASE_URL}/identity/verify", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print("跳过身份校验测试（用户注册失败）")
    print()

def test_health_check():
    print("=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_duplicate_registration():
    print("=== 测试重复注册 ===")
    data = {
        "Agent_name": "测试用户2026",
        "subtype": "user",
        "scope": {"doc": ["read"]},
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/identity/register/user", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    test_health_check()
    user_result = test_user_registration()
    test_bot_registration()
    test_identity_verify(user_result)
    test_duplicate_registration()
    print("=== 所有测试完成 ===")
