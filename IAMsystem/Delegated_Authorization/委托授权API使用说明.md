# 委托授权API 使用说明

## 功能概述
实现IAM系统的委托授权功能，支持静态授权和动态授权两种模式，分发AccessToken给合法的Agent。

## 启动方式
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

服务将运行在 `http://localhost:9000`

## 授权模式切换
在 `main.py` 中修改 `AUTH_MODE` 变量：
- `AUTH_MODE = "dynamic"`：动态授权模式，令牌有有效期，绑定申请IP
- `AUTH_MODE = "static"`：静态授权模式，令牌永久有效，IP为0.0.0.0

## API接口

### 1. 授权申请接口
- **地址**：`POST /IAMsystem/Delegated_Authorization`
- **请求格式**：
```json
{
    "AgentID": "Lark-doc-Agent",
    "Subtype": "user",
    "AgentSecret": "7s9KpR2tG8xQbA5dF3zC1vN4mH6jY0wU",
    "purpose": "查询企业内部数据",
    "scope": {"doc": ["read", "write"], "online": ["web_search"]},
    "time": 3600
}
```
- **参数说明**：
  - `AgentID`: Agent的英文名，必须是已注册的
  - `Subtype`: 身份类型，可选值 user/visitor/bot
  - `AgentSecret`: 注册时的密钥
  - `purpose`: 申请令牌的用途说明
  - `scope`: 权限范围，格式为dict(str, list(str))，数据类型支持doc/tablebase/calendar/online（与USERS_table.json中定义的一致），支持的操作：read/write/create/delete/web_search/fetch_content/analyze_content/all
  - `time`: 希望的有效期，单位秒，最大不超过86400(24小时)

- **返回格式**：
```json
{
    "AgentID": "Lark-doc-Agent",
    "status": 601,
    "AccessToken": {
        "token_id": "tk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "doc": ["read", "write"],
            "online": ["web_search"]
        },
        "AgentSecret": "新生成的随机密钥",
        "iat": 1777290183,
        "exp": 1777293783,
        "IP": "127.0.0.1",
        "purpose": "查询企业内部数据"
    }
}
```
- **状态码说明**：
  - 601：授权成功
  - 602：用户未注册或密钥错误
  - 603：权限不足
  - 604：未知错误

### 2. 健康检查接口
- **地址**：`GET /IAMsystem/Delegated_Authorization/health`
- **返回**：
```json
{
    "status": "healthy",
    "service": "Delegated-Authorization-API",
    "mode": "dynamic"
}
```

## 日志
日志文件存储在 `../Logs/Delegated_Authorization_Log/AccessToken_Auth.log`，格式为：
`[时间] [AgentID] [Subtype] 在 [ip] 申请 [scopen] 有效期到 [截止时间] 目的是 [purpose] 结果是 [status] 原因是 [status说明]`

## 数据存储
- 用户表：`../Storage/USERS_table.json` 存储已注册的Agent信息
- 令牌表：`../Storage/TOKENS_table.json` 存储已颁发的AccessToken，以`token_id`作为key，每个token_id对应一个AccessToken记录，支持同一Agent同时存在多个有效令牌

token存储示例

```json
{
    "tk_2e0ead1ba199495682e98001076e8180": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "doc": [
                "all"
            ],
            "tablebase": [
                "all"
            ],
            "calendar": [
                "all"
            ],
            "online": [
                "all"
            ]
        },
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "iat": 1777351882,
        "exp": 1777438282,
        "IP": "127.0.0.1",
        "purpose": "访问企业数据"
    },
    "tk_f3449be846bc42c6b734a3e750cd46a2": {
        "token_id": "tk_f3449be846bc42c6b734a3e750cd46a2",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "online": [
                "all"
            ]
        },
        "AgentSecret": "47058a448425430cb678f47883d315d586cc053e",
        "iat": 1777364339,
        "exp": 1777367339,
        "IP": "127.0.0.1",
        "purpose": "获取企业数据"
    }
}
```

