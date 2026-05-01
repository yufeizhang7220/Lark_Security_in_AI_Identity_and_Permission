# 身份注册 API 使用说明（v2.0）

本文档仅描述 API 接口的调用方式、请求/响应格式及状态码。

## 一、服务信息

- 根路径：`/IAMsystem/Identity_Registration`
- 默认端口：`9000`
- 完整地址：`http://localhost:9000/IAMsystem/Identity_Registration`

## 二、认证与通用说明

所有接口均需要 IP 白名单 或 API Key 认证（具体由 IAM 网关统一处理，身份注册模块不单独验证）。

请求体使用 `application/json`，响应体同样为 JSON。

时间戳统一使用 **秒级 Unix 时间戳（整数）**。

## 三、API 接口

### 3.1 用户注册（人或访客）

- **地址**：`POST /register`
- **功能**：注册一个普通用户或访客，写入 USERS\_table.json。

#### 请求体示例

```json
{
    "AgentID": "External-Search-Agent",
    "Subtype": "user",
    "scope": { "doc": ["read"], "online": ["web_search"] },
    "ip": "127.0.0.1"
}
```

#### 成功响应（HTTP 201）

```json
{
    "code": 201,
    "message": "注册成功",
    "data": {
        "AgentID": "External-Search-Agent",
        "Subtype": "user",
        "scope": { "doc": ["read"], "online": ["web_search"] },
        "AgentSecret": "a1b2c3d4e5f67890abcdef1234567890",
        "registered_at": 1745800000
    }
}
```

#### 失败响应（HTTP 400）

```json
{
    "code": 400,
    "message": "AgentID已存在",
    "data": null
}
```

### 3.2 机器注册（Agent 注册）

- **地址**：`POST /register/bot`
- **功能**：注册一个机器 Agent，同时写入 USERS\_table.json 和 BOTS\_table.json。

#### 请求体示例

```json
{
    "AgentID": "External-Search-Agent",
    "Subtype": "bot",
    "scope": { "online": ["all"] },
    "bot_description": "外部检索 Agent，负责从公开网站获取信息，无权访问飞书内部数据。",
    "apis": [
        {
            "api_id": "ext_search_query",
            "api": "localhost:8787/External-Search-Agent/api/query",
            "description": "根据关键词搜索网页",
            "method": "POST",
            "scope": { "online": ["all"] },
            "required_json": {},
            "output_json": {}
        },
        {
            "api_id": "ext_search_health",
            "api": "localhost:8787/External-Search-Agent/health",
            "method": "GET",
            "required_json": {},
            "output_json": {}
        }
    ],
    "ip": "127.0.0.1"
}
```

#### 成功响应（HTTP 201）

```json
{
    "code": 201,
    "message": "机器注册成功",
    "data": {
        "AgentID": "External-Search-Agent",
        "Subtype": "bot",
        "scope": { "online": ["all"] },
        "AgentSecret": "7s9KpR2tG8xQbA5dF4zC1vN4mH6jY0wU",
        "registered_at": 1745800000
    }
}
```

#### 失败响应（HTTP 400）

```json
{
    "code": 400,
    "message": "缺少必填字段 或 AgentID已存在",
    "data": null
}
```

### 3.3 查询机器 API 信息（通过 api\_id）

- **地址**：`GET /bot/{AgentID}/api/{api_id}`
- **功能**：返回指定 Agent 的指定 API 的详细信息，供调用模块动态获取。

#### 响应（HTTP 200）

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

#### 失败响应（HTTP 404）

```json
{
    "code": 404,
    "message": "Agent 或 api_id 不存在",
    "data": null
}
```

### 3.4 健康检查

- **地址**：`GET /health`

#### 响应

```json
{
    "status": "healthy",
    "service": "Identity-Registration-API"
}
```

## 四、状态码说明

| HTTP 状态码 | code 字段 | 含义               |
| -------- | ------- | ---------------- |
| 201      | 201     | 注册成功             |
| 200      | 200     | 查询成功             |
| 400      | 400     | 参数错误、缺少字段、ID 已存在 |
| 404      | 404     | 资源不存在            |
| 500      | 500     | 服务器内部错误（如文件写入失败） |

