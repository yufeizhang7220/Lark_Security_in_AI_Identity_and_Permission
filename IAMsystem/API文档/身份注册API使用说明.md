# 身份注册 API 使用说明（v2.0）

本文档描述身份注册模块的 API 接口调用方式、请求/响应格式及状态码。

## 一、服务信息

- **根路径**：`/IAMsystem/identity`
- **默认端口**：9002
- **完整地址**：`http://localhost:9002/IAMsystem/identity`
- **API文档**：`http://localhost:9002/docs`

## 二、认证与通用说明

- 所有接口均需要 IP 白名单 或 API Key 认证（具体由 IAM 网关统一处理）
- 请求体使用 `application/json`，响应体同样为 JSON
- 时间戳统一使用 **秒级 Unix 时间戳**（整数）
- 密钥采用 bcrypt 加密存储，不可逆

## 三、API 接口

### 3.1 用户/访客注册

**地址**：`POST /register/user`

**功能**：注册一个普通用户或访客

**请求参数**：

| 字段          | 类型     | 必填 | 说明                      |
| ----------- | ------ | -- | ----------------------- |
| Agent\_name | string | 是  | 用户名称，全局唯一               |
| subtype     | string | 是  | 身份类型：`user` / `visitor` |
| scope       | object | 是  | 权限集合，JSON对象             |
| ip          | string | 否  | 注册IP地址，默认 `127.0.0.1`   |

**请求示例**：

```json
{
    "Agent_name": "张三",
    "subtype": "user",
    "scope": { "doc": ["read", "write"], "online": ["web_search"] },
    "ip": "192.168.1.100"
}
```

**成功响应（HTTP 201）**：

```json
{
    "code": 201,
    "message": "success",
    "data": {
        "Agent_name": "张三",
        "subtype": "user",
        "scope": { "doc": ["read", "write"], "online": ["web_search"] },
        "agent_id": "user_1777000000_abc123",
        "agent_secret": "32位随机密钥",
        "registered_at": 1777000000
    }
}
```

**失败响应（HTTP 400）**：

```json
{
    "code": 400,
    "message": "Agent名称已存在",
    "data": null
}
```

***

### 3.2 机器 Agent 注册

**地址**：`POST /register/bot`

**功能**：注册一个机器 Agent

**请求参数**：

| 字段            | 类型     | 必填 | 说明              |
| ------------- | ------ | -- | --------------- |
| Bot\_name     | string | 是  | Bot名称，全局唯一      |
| Bot\_id       | string | 否  | 自定义BotID，系统自动生成 |
| scope         | object | 是  | Bot自身权限集合       |
| sub\_scope    | object | 否  | 不同身份的权限映射表      |
| api\_endpoint | string | 否  | Bot服务地址         |
| ip            | string | 否  | 注册IP地址          |

**请求示例**：

```json
{
    "Bot_name": "外部检索Agent",
    "scope": { "online": ["web_search", "fetch_content"], "iam": ["verify_token"] },
    "sub_scope": {
        "user": { "online": ["web_search", "fetch_content"] },
        "visitor": { "online": ["web_search"] }
    },
    "api_endpoint": "http://localhost:8002/api",
    "ip": "127.0.0.1"
}
```

**成功响应（HTTP 201）**：

```json
{
    "code": 201,
    "message": "success",
    "data": {
        "Agent_name": "外部检索Agent",
        "subtype": "bot",
        "scope": { "online": ["web_search", "fetch_content"], "iam": ["verify_token"] },
        "agent_id": "bot_1777000000_xyz789",
        "agent_secret": "32位随机密钥",
        "registered_at": 1777000000
    }
}
```

**失败响应（HTTP 400）**：

```json
{
    "code": 400,
    "message": "Bot名称已存在",
    "data": null
}
```

***

### 3.3 身份校验

**地址**：`POST /verify`

**功能**：校验 AgentID 和 AgentSecret 的合法性

**请求参数**：

| 字段            | 类型     | 必填 | 说明        |
| ------------- | ------ | -- | --------- |
| agent\_id     | string | 是  | 系统生成的唯一ID |
| agent\_secret | string | 是  | 注册时返回的密钥  |

**请求示例**：

```json
{
    "agent_id": "user_1777000000_abc123",
    "agent_secret": "5e954448ab0c7e05cda70e37ac015b9e"
}
```

**成功响应（HTTP 200）**：

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "valid": true,
        "scope": { "doc": ["read", "write"], "online": ["web_search"] }
    }
}
```

**失败响应（HTTP 401）**：

```json
{
    "code": 401,
    "message": "身份验证失败",
    "data": null
}
```

***

### 3.4 健康检查

**地址**：`GET /health`（完整路径：`http://localhost:9002/IAMsystem/identity/health`）

**响应**：

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "status": "healthy"
    }
}
```

## 四、状态码说明

| HTTP状态码 | code字段 | 含义               |
| ------- | ------ | ---------------- |
| 200     | 200    | 查询成功             |
| 201     | 201    | 注册成功             |
| 400     | 400    | 参数错误、缺少字段、ID已存在  |
| 401     | 401    | 身份验证失败（密钥错误、凭证无效）           |
| 403     | 403    | 操作被拦截（IP/Agent在黑名单、权限不足） |
| 500     | 500    | 服务器内部错误（如文件写入失败） |

## 五、权限 scope 说明

scope 采用 `"资源类型:操作列表"` 的键值对结构：

```json
{
    "doc": ["read", "write", "delete"],
    "indata": ["read_contact", "read_calendar", "read_bitable"],
    "online": ["web_search", "fetch_content", "analyze_content"],
    "iam": ["apply_token", "verify_token"]
}
```

**预定义资源类型**：

- `doc`：飞书文档操作权限
- `indata`：企业内部数据访问权限
- `online`：外部网络访问权限
- `iam`：IAM系统自身操作权限

## 六、日志说明

日志文件位于 `Logs/Identity_Registration_Log/` 目录，按日期分割：

```
Logs/Identity_Registration_Log/registration_YYYYMMDD.log
```

**日志格式（JSON格式，一行一条）**：

```json
{
    "log_id": "uuid",
    "timestamp": 1777000000000,
    "agent_id": "user_xxx",
    "agent_name": "用户名",
    "ip": "192.168.1.100",
    "operation": "register",
    "status": "success",
    "detail": {
        "subtype": "user",
        "scope": { "doc": ["read"] },
        "agent_secret": "****"
    }
}
```

**operation 类型**：

- `register`：注册操作
- `verify`：校验操作

**status 类型**：

- `success`：成功
- `fail`：失败
- `blocked`：拦截

***

## 七、相关文件

| 文件                | 说明        |
| ----------------- | --------- |
| `config.py`       | 配置文件      |
| `storage.py`      | 存储操作模块    |
| `audit_logger.py` | 审计日志模块    |
| `app.py`          | API接口实现   |
| `main.py`         | FastAPI入口 |

***

**文档版本**：v2.0
**最后更新**：2026-05-05
**维护者**：赵瑞利
