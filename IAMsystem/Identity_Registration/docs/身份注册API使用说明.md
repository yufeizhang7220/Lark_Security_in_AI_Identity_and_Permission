# 身份注册模块 (Identity Registration) 使用说明

## 一、项目简介

身份注册模块是飞书AI身份与权限系统的核心组件，负责管理所有Agent和用户的注册流程。本模块为其他模块（委托授权模块、请求调用模块）提供身份注册服务。

**核心功能：**
- 用户注册：注册普通用户或访客
- 机器注册：注册机器Agent，同时记录API信息
- API查询：查询指定Agent的API详情
- 日志记录：记录所有注册操作，支持审计追溯
- 健康检查：检查服务状态

## 二、快速开始

### 2.1 环境要求

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic

### 2.2 安装依赖

```bash
cd d:\py\code\.vscode\ctf project\Identity_Registration
pip install -r requirements.txt
```

### 2.3 启动服务

```bash
python main.py
```

服务启动后显示：
```
启动身份注册服务: http://0.0.0.0:9000
API文档: http://localhost:9000/docs
健康检查: http://localhost:9000/health
注册接口: POST http://localhost:9000/IAMsystem/Identity_Registration/register
机器注册: POST http://localhost:9000/IAMsystem/Identity_Registration/register/bot
查询API: GET http://localhost:9000/IAMsystem/Identity_Registration/bot/{AgentID}/api/{api_id}
```

### 2.4 访问API文档

打开浏览器访问：`http://localhost:9000/docs`

可以可视化管理所有API接口，直接在网页上测试。

## 三、API接口详解

### 3.1 用户注册

**接口地址：** `POST /IAMsystem/Identity_Registration/register`

**功能：** 注册一个普通用户或访客

**请求参数：**
```json
{
    "AgentID": "Agent的ID（唯一标识）",
    "Subtype": "user/visitor",
    "scope": {
        "doc": ["read"],
        "online": ["web_search"]
    },
    "ip": "注册IP地址"
}
```

**请求示例：**
```bash
curl -X POST "http://localhost:9000/IAMsystem/Identity_Registration/register" \
  -H "Content-Type: application/json" \
  -d '{
    "AgentID": "MyAgent",
    "Subtype": "user",
    "scope": {"doc": ["read"], "online": ["web_search"]},
    "ip": "127.0.0.1"
  }'
```

**成功响应 (201)：**
```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "AgentID": "MyAgent",
        "Subtype": "user",
        "scope": {
            "doc": ["read"],
            "online": ["web_search"]
        },
        "AgentSecret": "a1b2c3d4e5f67890abcdef1234567890",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

**失败响应 (400)：**
```json
{
    "code": 400,
    "message": "AgentID已存在",
    "data": null
}
```

---

### 3.2 机器注册（Agent注册）

**接口地址：** `POST /IAMsystem/Identity_Registration/register/bot`

**功能：** 注册一个机器Agent，同时写入用户表和机器表

**请求参数：**
```json
{
    "AgentID": "Agent的ID（唯一标识）",
    "Subtype": "bot",
    "scope": {
        "doc": ["read"],
        "online": ["all"]
    },
    "bot_description": "机器人的描述",
    "apis": [
        {
            "api_id": "api的唯一标识",
            "api": "localhost:8787/MyAgent/api/query",
            "description": "API功能描述",
            "method": "POST/GET",
            "scope": {},
            "required_json": {},
            "output_json": {}
        }
    ],
    "ip": "注册IP地址"
}
```

**请求示例：**
```bash
curl -X POST "http://localhost:9000/IAMsystem/Identity_Registration/register/bot" \
  -H "Content-Type: application/json" \
  -d '{
    "AgentID": "MyBot",
    "Subtype": "bot",
    "scope": {"online": ["all"]},
    "bot_description": "我的机器人，负责搜索网页内容",
    "apis": [
        {
            "api_id": "search_web",
            "api": "localhost:8787/MyBot/api/search",
            "description": "搜索网页内容",
            "method": "POST",
            "scope": {"online": ["all"]},
            "required_json": {"query": "搜索关键词"},
            "output_json": {"results": []}
        }
    ],
    "ip": "127.0.0.1"
  }'
```

**成功响应 (201)：**
```json
{
    "code": 201,
    "message": "机器注册成功",
    "data": {
        "AgentID": "MyBot",
        "Subtype": "bot",
        "scope": {"online": ["all"]},
        "AgentSecret": "7s9KpR2tG8xQbA5dF4zC1vN4mH6jY0wU",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

---

### 3.3 查询机器API信息

**接口地址：** `GET /IAMsystem/Identity_Registration/bot/{AgentID}/api/{api_id}`

**功能：** 查询指定Agent的指定API详情

**路径参数：**
- `AgentID`：Agent的ID
- `api_id`：API的唯一标识

**请求示例：**
```bash
curl "http://localhost:9000/IAMsystem/Identity_Registration/bot/MyBot/api/search_web"
```

**成功响应 (200)：**
```json
{
    "code": 200,
    "data": {
        "api_id": "search_web",
        "api": "localhost:8787/MyBot/api/search",
        "method": "POST",
        "description": "搜索网页内容",
        "scope": {"online": ["all"]},
        "required_json": {"query": "搜索关键词"},
        "output_json": {"results": []}
    }
}
```

**失败响应 (404)：**
```json
{
    "code": 404,
    "message": "Agent 或 api_id 不存在",
    "data": null
}
```

---

### 3.4 健康检查

**接口地址：** `GET /IAMsystem/Identity_Registration/health`

**功能：** 检查服务是否正常运行

**请求示例：**
```bash
curl "http://localhost:9000/IAMsystem/Identity_Registration/health"
```

**响应：**
```json
{
    "status": "healthy",
    "service": "Identity-Registration-API"
}
```

## 四、日志功能

### 4.1 日志文件位置

日志文件保存在：`Logs/Identity_Registration_Log/registration.log`

### 4.2 日志格式

符合团队项目要求的格式：
```
[时间] [谁] 在 [ip] 注册 [身份] 权限 [权限范围] [其他信息] 结果 [status] 原因 [message]
```

### 4.3 日志示例

**用户注册成功：**
```
[2026-05-01 10:16:40] [ZhangSan] 在 [192.168.1.50] 注册 [user] 权限 {"doc": ["read"]} 结果 201 原因 注册成功
```

**机器注册成功：**
```
[2026-05-01 10:16:50] [SearchBot] 在 [192.168.1.50] 注册 [bot] 权限 {"online": ["all"]} 描述:搜索机器人，负责搜索网页内容, APIs数量:1 结果 201 原因 机器注册成功
```

**AgentID已存在（失败）：**
```
[2026-05-01 10:17:00] [ZhangSan] 在 [192.168.1.50] 注册 [user] 权限 {"doc": ["read"]} 结果 400 原因 AgentID已存在
```

### 4.4 查看日志

在PowerShell中查看：
```powershell
Get-Content "d:\py\code\.vscode\ctf project\Identity_Registration\Logs\Identity_Registration_Log\registration.log" -Tail 10
```

实时跟踪日志：
```powershell
Get-Content "d:\py\code\.vscode\ctf project\Identity_Registration\Logs\Identity_Registration_Log\registration.log" -Wait -Tail 10
```

## 五、状态码说明

| HTTP状态码 | code字段 | 含义 |
|------------|----------|------|
| 201 | 201 | 注册成功 |
| 200 | 200 | 查询成功 |
| 400 | 400 | 参数错误、缺少字段、ID已存在 |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误（如文件写入失败） |

## 六、存储文件格式

### 6.1 USERS_table.json

**路径：** `Storage/USERS_table.json`

**格式：**
```json
{
    "AgentID": {
        "AgentID": "str - Agent唯一标识",
        "Subtype": "str - user/visitor/bot",
        "scope": {
            "doc": ["read/write/all"],
            "tablebase": ["read/write/all"],
            "calendar": ["read/write/all"],
            "online": ["web_search/fetch_content/analyze_content/all"]
        },
        "AgentSecret": "str - 注册时生成的密钥",
        "registered_at": 1745800000,
        "ip": "127.0.0.1"
    }
}
```

**说明：**
- `registered_at`：Unix时间戳（秒）
- `AgentSecret`：系统自动生成的32位密钥
- `scope`：权限范围，支持 doc/tablebase/calendar/online

### 6.2 BOTS_table.json

**路径：** `Storage/BOTS_table.json`

**格式：**
```json
{
    "AgentID": {
        "bot_name": "str - Bot名称",
        "bot_description": "str - Bot功能描述",
        "API_adderess": [
            {
                "api_id": "str - API唯一标识",
                "api": "str - API访问地址",
                "description": "str - API功能描述",
                "method": "POST/GET",
                "scope": {},
                "required_json": {},
                "output_json": {}
            }
        ]
    }
}
```

**说明：**
- `api_id`：每个API的唯一标识，供其他模块查询使用
- `scope`：API的权限范围
- `required_json`：请求参数格式说明
- `output_json`：响应数据格式说明

## 七、Python调用示例

### 7.1 安装依赖

```python
pip install requests
```

### 7.2 完整调用示例

```python
import requests
import json

BASE_URL = "http://localhost:9000/IAMsystem/Identity_Registration"

# 1. 健康检查
def health_check():
    response = requests.get(f"{BASE_URL}/health")
    print(f"健康检查: {response.json()}")

# 2. 用户注册
def register_user():
    data = {
        "AgentID": "TestAgent",
        "Subtype": "user",
        "scope": {"doc": ["read"], "online": ["web_search"]},
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"用户注册: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()

# 3. 机器注册
def register_bot():
    data = {
        "AgentID": "SearchBot",
        "Subtype": "bot",
        "scope": {"online": ["all"]},
        "bot_description": "搜索机器人，负责搜索网页内容",
        "apis": [
            {
                "api_id": "web_search",
                "api": "localhost:8787/SearchBot/api/search",
                "description": "搜索网页",
                "method": "POST",
                "scope": {"online": ["all"]},
                "required_json": {"query": "str - 搜索关键词"},
                "output_json": {"results": []}
            }
        ],
        "ip": "127.0.0.1"
    }
    response = requests.post(f"{BASE_URL}/register/bot", json=data)
    print(f"机器注册: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()

# 4. 查询API
def query_api():
    response = requests.get(f"{BASE_URL}/bot/SearchBot/api/web_search")
    print(f"查询API: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    health_check()
    register_user()
    register_bot()
    query_api()
```

## 八、与其他模块的交互

### 8.1 依赖关系

```
┌─────────────────┐
│ 身份注册模块    │  ← 本模块
│ (Identity_Registration) │
└────────┬────────┘
         │
         ├──写入──→ USERS_table.json
         │          ↑ 读取
         │  ┌──────┴───────┐
         │  │              │
    ┌────▼──▼────┐  ┌────▼───▼────┐
    │ 委托授权模块 │  │ 请求调用模块 │
    │ (Delegated_Authorization) │
    └────────────┘  └──────────────┘
```

### 8.2 数据提供

- **委托授权模块**：读取 USERS_table.json，验证Agent身份
- **请求调用模块**：读取 BOTS_table.json，获取API信息

## 九、注意事项

1. **AgentID唯一性**：每个AgentID必须唯一，注册前请先查询是否已存在
2. **密钥保存**：注册成功后返回的AgentSecret请妥善保存，后续授权需要使用
3. **IP白名单**：建议记录注册时的IP地址，用于安全验证
4. **时间戳格式**：registered_at使用Unix时间戳（秒级）
5. **scope格式**：权限范围必须是字典格式，key为资源类型，value为操作列表
6. **日志审计**：所有注册操作都会记录到日志文件，支持审计追溯

## 十、常见问题

### Q1: 注册时提示"AgentID已存在"？
A: 该AgentID已被注册，请使用新的ID，或先查询现有Agent。

### Q2: 如何修改已注册Agent的信息？
A: 当前版本不支持修改，请先删除再重新注册。

### Q3: 注册成功后AgentSecret丢失怎么办？
A: AgentSecret无法找回，请删除该Agent并重新注册。

### Q4: 机器注册时apis数组可以为空吗？
A: 可以，但建议至少注册一个API，以便其他模块调用。

### Q5: 如何查看所有已注册的Agent？
A: 直接查看 Storage/USERS_table.json 和 Storage/BOTS_table.json 文件。

### Q6: 日志文件在哪里？如何查看？
A: 日志文件在 Logs/Identity_Registration_Log/registration.log，使用 Get-Content -Wait -Tail 10 实时跟踪。

### Q7: 日志格式是什么？
A: 格式为：[时间] [谁] 在 [ip] 注册 [身份] 权限 [权限范围] [其他信息] 结果 [status] 原因 [message]

## 十一、文件结构

```
Identity_Registration/
├── config.py                   # 配置文件
├── storage.py                  # 存储操作模块
├── app.py                      # API主逻辑（含日志功能）
├── main.py                     # FastAPI入口
├── requirements.txt            # 依赖
├── test_api.py                 # 测试脚本
├── README.md                   # 英文说明
├── 使用说明.md                 # 中文详细使用说明（队友专用）
├── Logs/
│   └── Identity_Registration_Log/
│       └── registration.log    # 注册日志（审计追溯用）
└── Storage/
    ├── USERS_table.json       # 用户表
    └── BOTS_table.json       # 机器表
```

## 十二、联系方式

- 维护者：赵瑞利
- 模块：身份注册模块 & 外部检索Agent
- 版本：v2.0
- 更新日期：2026-05-01

---

**如有问题，请联系维护者或在团队群中提问。**
