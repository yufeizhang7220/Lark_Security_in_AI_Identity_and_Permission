# 身份注册模块 (Identity Registration)

## 功能概述

身份注册模块是飞书AI身份与权限系统的核心组件，负责管理所有Agent和用户的注册流程。

## 核心功能

- **用户注册** (`POST /register`): 注册普通用户或访客
- **机器注册** (`POST /register/bot`): 注册机器Agent，同时写入USERS_table.json和BOTS_table.json
- **API查询** (`GET /bot/{AgentID}/api/{api_id}`): 查询指定Agent的API信息
- **健康检查** (`GET /health`): 检查服务状态

## 项目结构

```
Identity_Registration/
├── config.py          # 配置文件
├── storage.py         # 存储操作模块
├── app.py             # API主逻辑
├── main.py            # FastAPI入口
├── requirements.txt   # 依赖
├── Storage/           # 存储目录
│   ├── USERS_table.json
│   └── BOTS_table.json
└── README.md
```

## 安装依赖

```bash
cd d:\py\code\.vscode\ctf project\Identity_Registration
pip install -r requirements.txt
```

## 启动服务

```bash
python main.py
```

服务将运行在 `http://localhost:9000`

## API接口

### 1. 用户注册

**地址**: `POST /IAMsystem/Identity_Registration/register`

**请求体**:
```json
{
    "AgentID": "External-Search-Agent",
    "Subtype": "user",
    "scope": { "doc": ["read"], "online": ["web_search"] },
    "ip": "127.0.0.1"
}
```

**成功响应** (201):
```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "AgentID": "External-Search-Agent",
        "Subtype": "user",
        "scope": { "doc": ["read"], "online": ["web_search"] },
        "AgentSecret": "a1b2c3d4e5f67890abcdef1234567890",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

**失败响应** (400):
```json
{
    "code": 400,
    "message": "AgentID已存在",
    "data": null
}
```

### 2. 机器注册

**地址**: `POST /IAMsystem/Identity_Registration/register/bot`

**请求体**:
```json
{
    "AgentID": "External-Search-Agent",
    "Subtype": "bot",
    "scope": { "online": ["all"] },
    "bot_description": "外部检索 Agent，负责从公开网站获取信息。",
    "apis": [
        {
            "api_id": "ext_search_query",
            "api": "localhost:8787/External-Search-Agent/api/query",
            "description": "根据关键词搜索网页",
            "method": "POST",
            "scope": { "online": ["all"] },
            "required_json": {},
            "output_json": {}
        }
    ],
    "ip": "127.0.0.1"
}
```

**成功响应** (201):
```json
{
    "code": 201,
    "message": "机器注册成功",
    "data": {
        "AgentID": "External-Search-Agent",
        "Subtype": "bot",
        "scope": { "online": ["all"] },
        "AgentSecret": "7s9KpR2tG8xQbA5dF4zC1vN4mH6jY0wU",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

### 3. 查询机器API信息

**地址**: `GET /IAMsystem/Identity_Registration/bot/{AgentID}/api/{api_id}`

**成功响应** (200):
```json
{
    "code": 200,
    "data": {
        "api_id": "ext_search_query",
        "api": "localhost:8787/External-Search-Agent/api/query",
        "method": "POST",
        "description": "根据关键词搜索网页",
        "scope": { "online": ["all"] },
        "required_json": {},
        "output_json": {}
    }
}
```

**失败响应** (404):
```json
{
    "code": 404,
    "message": "Agent 或 api_id 不存在",
    "data": null
}
```

### 4. 健康检查

**地址**: `GET /IAMsystem/Identity_Registration/health`

**响应**:
```json
{
    "status": "healthy",
    "service": "Identity-Registration-API"
}
```

## 状态码说明

| HTTP状态码 | code字段 | 含义 |
|------------|----------|------|
| 201 | 201 | 注册成功 |
| 200 | 200 | 查询成功 |
| 400 | 400 | 参数错误、缺少字段、ID已存在 |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误 |

## 存储格式

### USERS_table.json

```json
{
    "AgentID": {
        "AgentID": "str",
        "Subtype": "user/bot/visitor",
        "scope": { "doc": ["read"], "online": ["all"] },
        "AgentSecret": "str",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

### BOTS_table.json

```json
{
    "AgentID": {
        "bot_name": "str",
        "bot_description": "str",
        "API_adderess": [
            {
                "api_id": "str",
                "api": "str",
                "description": "str",
                "method": "POST/GET",
                "scope": {},
                "required_json": {},
                "output_json": {}
            }
        ]
    }
}
```

## 使用示例

### cURL

**用户注册**:
```bash
curl -X POST "http://localhost:9000/IAMsystem/Identity_Registration/register" -H "Content-Type: application/json" -d "{\"AgentID\":\"Test-Agent\",\"Subtype\":\"user\",\"scope\":{\"doc\":[\"read\"]},\"ip\":\"127.0.0.1\"}"
```

**机器注册**:
```bash
curl -X POST "http://localhost:9000/IAMsystem/Identity_Registration/register/bot" -H "Content-Type: application/json" -d "{\"AgentID\":\"Test-Bot\",\"Subtype\":\"bot\",\"scope\":{\"online\":[\"all\"]},\"bot_description\":\"测试机器人\",\"apis\":[{\"api_id\":\"test_query\",\"api\":\"localhost:8787/test/api\",\"method\":\"POST\",\"scope\":{}}],\"ip\":\"127.0.0.1\"}"
```

**查询API**:
```bash
curl "http://localhost:9000/IAMsystem/Identity_Registration/bot/Test-Bot/api/test_query"
```

### Python

```python
import requests

base_url = "http://localhost:9000/IAMsystem/Identity_Registration"

# 用户注册
user_data = {
    "AgentID": "Test-Agent",
    "Subtype": "user",
    "scope": {"doc": ["read"]},
    "ip": "127.0.0.1"
}
response = requests.post(f"{base_url}/register", json=user_data)
print(response.json())

# 机器注册
bot_data = {
    "AgentID": "Test-Bot",
    "Subtype": "bot",
    "scope": {"online": ["all"]},
    "bot_description": "测试机器人",
    "apis": [
        {
            "api_id": "test_query",
            "api": "localhost:8787/test/api",
            "method": "POST",
            "scope": {}
        }
    ],
    "ip": "127.0.0.1"
}
response = requests.post(f"{base_url}/register/bot", json=bot_data)
print(response.json())

# 查询API
response = requests.get(f"{base_url}/bot/Test-Bot/api/test_query")
print(response.json())
```

## 维护者

赵瑞利（外部检索 Agent & 身份注册模块）

## 版本

v2.0 - 2026-04-29
