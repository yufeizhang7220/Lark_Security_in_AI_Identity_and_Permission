"""
测试身份注册 API
"""

import requests
import json

BASE_URL = "http://localhost:9000/IAMsystem/Identity_Registration"

def test_user_registration():
    """测试用户注册"""
    print("=== 测试用户注册 ===")
    data = {
        "AgentID": "Test-User",
        "Subtype": "user",
        "scope": {"doc": ["read"], "online": ["web_search"]},
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_bot_registration():
    """测试机器注册"""
    print("=== 测试机器注册 ===")
    data = {
        "AgentID": "Test-Bot",
        "Subtype": "bot",
        "scope": {"online": ["all"]},
        "bot_description": "测试机器人，负责从公开网站获取信息。",
        "apis": [
            {
                "api_id": "test_query",
                "api": "localhost:8787/Test-Bot/api/query",
                "description": "测试查询接口",
                "method": "POST",
                "scope": {"online": ["all"]},
                "required_json": {},
                "output_json": {}
            },
            {
                "api_id": "test_health",
                "api": "localhost:8787/Test-Bot/health",
                "method": "GET",
                "required_json": {},
                "output_json": {}
            }
        ],
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/register/bot", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_get_bot_api():
    """测试查询机器API信息"""
    print("=== 测试查询机器API信息 ===")
    response = requests.get(f"{BASE_URL}/bot/Test-Bot/api/test_query")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_health():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_duplicate_registration():
    """测试重复注册"""
    print("=== 测试重复注册 ===")
    data = {
        "AgentID": "Test-User",
        "Subtype": "user",
        "scope": {"doc": ["read"]},
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

def test_not_found():
    """测试资源不存在"""
    print("=== 测试资源不存在 ===")
    response = requests.get(f"{BASE_URL}/bot/NonExistent/api/test_query")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    print("开始测试身份注册 API...\n")

    try:
        test_health()
        test_user_registration()
        test_bot_registration()
        test_get_bot_api()
        test_duplicate_registration()
        test_not_found()
        print("所有测试完成！")
    except Exception as e:
        print(f"测试失败: {e}")
