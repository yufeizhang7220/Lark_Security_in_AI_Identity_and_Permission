# 审计追溯模块 API 使用说明

## 一、概述

审计追溯模块负责记录系统中所有操作日志，提供异常行为检测能力，并支持日志查询和导出功能。所有接口统一前缀：`http://localhost:9000/IAMsystem/audit`

## 二、统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 三、错误码说明

| 错误码 | 说明 |
| :--- | :--- |
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 身份验证失败 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 四、API 接口列表

### 4.1 审计日志校验

**接口地址**：`POST /logs`

**功能描述**：校验操作是否合法，检测异常行为

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 是 | 操作主体 AgentID |
| start_time | int | 是 | 查询开始时间戳（毫秒） |
| end_time | int | 是 | 查询结束时间戳（毫秒） |
| operation | string | 是 | 操作类型（register/authorize/verify） |
| detail | object | 是 | 操作详情 |

**请求示例**：

```json
{
  "agent_id": "DocAgent",
  "start_time": 1745800000000,
  "end_time": 1745803600000,
  "operation": "authorize",
  "detail": {
    "ip": "127.0.0.1",
    "token_id": "jti-xxx",
    "applied_scope": {"doc": ["write"]}
  }
}
```

**响应示例**：

```json
{
  "valid": true,
  "fail_reason": ""
}
```

---

### 4.2 记录通用日志

**接口地址**：`POST /record`

**功能描述**：记录通用操作日志

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 是 | 操作主体 AgentID |
| ip | string | 是 | 操作 IP 地址 |
| operation | string | 是 | 操作类型 |
| status | string | 否 | 操作状态（success/fail/blocked），默认 success |
| detail | object | 是 | 操作详情 |

**请求示例**：

```json
{
  "agent_id": "DataAgent",
  "ip": "127.0.0.1",
  "operation": "data_query",
  "status": "success",
  "detail": {
    "table_id": "tbl-xxx",
    "query_type": "read_bitable"
  }
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "日志记录成功",
  "data": {
    "log_id": "uuid-xxx"
  }
}
```

---

### 4.3 记录身份注册日志

**接口地址**：`POST /record/registration`

**功能描述**：记录身份注册操作日志

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 是 | 注册的 AgentID |
| ip | string | 是 | 请求 IP 地址 |
| subtype | string | 是 | 身份类型（user/bot/visitor） |
| scope | object | 是 | 权限范围 |
| agent_secret | string | 是 | 掩码后的密钥 |
| status | string | 否 | 操作状态（success/fail），默认 success |
| fail_reason | string | 否 | 失败原因 |

**请求示例**：

```json
{
  "agent_id": "DocAgent",
  "ip": "127.0.0.1",
  "subtype": "bot",
  "scope": {"doc": ["read", "write"], "indata": ["read"]},
  "agent_secret": "******",
  "status": "success"
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "注册日志记录成功",
  "data": {
    "log_id": "uuid-xxx"
  }
}
```

---

### 4.4 记录委托授权日志

**接口地址**：`POST /record/authorization`

**功能描述**：记录 AccessToken 申请授权日志

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 是 | 申请 Token 的 AgentID |
| ip | string | 是 | 请求 IP 地址 |
| token_id | string | 是 | Token 的 jti 值 |
| applied_scope | object | 是 | 申请的权限范围 |
| granted_scope | object | 是 | 实际授予的权限范围 |
| expire_at | int | 是 | Token 过期时间戳 |
| status | string | 否 | 操作状态（success/fail），默认 success |
| fail_reason | string | 否 | 失败原因 |

**请求示例**：

```json
{
  "agent_id": "DocAgent",
  "ip": "127.0.0.1",
  "token_id": "jti-xxx",
  "applied_scope": {"doc": ["write"], "indata": ["read"]},
  "granted_scope": {"doc": ["write"], "indata": ["read"]},
  "expire_at": 1745803600,
  "status": "success"
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "授权日志记录成功",
  "data": {
    "log_id": "uuid-xxx"
  }
}
```

---

### 4.5 记录权限校验日志

**接口地址**：`POST /record/verification`

**功能描述**：记录 Token 权限校验日志

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 是 | 校验主体 AgentID |
| ip | string | 是 | 请求 IP 地址 |
| token_id | string | 是 | Token 的 jti 值 |
| required_scope | object | 是 | 所需权限范围 |
| valid | boolean | 否 | 校验是否通过，默认 true |
| fail_reason | string | 否 | 失败原因 |

**请求示例**：

```json
{
  "agent_id": "DataAgent",
  "ip": "127.0.0.1",
  "token_id": "jti-xxx",
  "required_scope": {"indata": ["read_bitable"]},
  "valid": true
}
```

**响应示例**：

```json
{
  "code": 200,
  "message": "验证日志记录成功",
  "data": {
    "log_id": "uuid-xxx"
  }
}
```

---

### 4.6 导出日志

**接口地址**：`GET /export`

**功能描述**：按时间范围导出审计日志

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| start_time | int | 是 | 查询开始时间戳（毫秒） |
| end_time | int | 是 | 查询结束时间戳（毫秒） |

**请求示例**：

```
GET /export?start_time=1745800000000&end_time=1745803600000
```

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "log_id": "uuid-xxx",
      "timestamp": 1745800000000,
      "agent_id": "DocAgent",
      "ip": "127.0.0.1",
      "operation": "authorize",
      "status": "success",
      "detail": {
        "token_id": "jti-xxx",
        "applied_scope": {"doc": ["write"]},
        "granted_scope": {"doc": ["write"]},
        "expire_at": 1745803600
      }
    }
  ]
}
```

---

### 4.7 查询黑名单

**接口地址**：`GET /blacklist`

**功能描述**：获取黑名单列表

**请求参数**：无

**响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "agents": ["BadAgent"],
    "ips": ["192.168.1.100"],
    "users": ["user123"]
  }
}
```

---

### 4.8 添加到黑名单

**接口地址**：`POST /blacklist/add`

**功能描述**：将 Agent、IP 或用户加入黑名单

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 否 | AgentID |
| ip | string | 否 | IP 地址 |
| user_id | string | 否 | 用户 ID |

**请求示例**：

```
POST /blacklist/add?agent_id=BadAgent&ip=192.168.1.100
```

**响应示例**：

```json
{
  "code": 200,
  "message": "已加入黑名单"
}
```

---

### 4.9 从黑名单移除

**接口地址**：`POST /blacklist/remove`

**功能描述**：从黑名单中移除 Agent、IP 或用户

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| agent_id | string | 否 | AgentID |
| ip | string | 否 | IP 地址 |
| user_id | string | 否 | 用户 ID |

**请求示例**：

```
POST /blacklist/remove?agent_id=BadAgent
```

**响应示例**：

```json
{
  "code": 200,
  "message": "已从黑名单移除"
}
```

---

### 4.10 健康检查

**接口地址**：`GET /health`

**功能描述**：检查服务健康状态

**请求参数**：无

**响应示例**：

```json
{
  "status": "healthy",
  "service": "Audit-Trail-API"
}
```

---

## 五、审计日志结构

### 5.1 日志基础结构

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| log_id | string | 唯一日志 ID |
| timestamp | int64 | 时间戳（毫秒） |
| agent_id | string | 操作主体 AgentID |
| ip | string | 操作 IP 地址 |
| operation | string | 操作类型（register/authorize/verify） |
| status | string | 操作结果（success/fail/blocked） |
| detail | object | 操作详情 |

### 5.2 身份注册日志详情

```json
{
  "subtype": "user/bot/visitor",
  "scope": {"doc": ["read"]},
  "agent_secret": "掩码后的密钥",
  "fail_reason": "失败原因"
}
```

### 5.3 委托授权日志详情

```json
{
  "token_id": "jti字段值",
  "applied_scope": {"doc": ["write"]},
  "granted_scope": {"doc": ["write"]},
  "expire_at": 1745803600,
  "fail_reason": "权限不足"
}
```

### 5.4 权限校验日志详情

```json
{
  "token_id": "jti字段值",
  "required_scope": {"indata": ["read"]},
  "valid": true,
  "fail_reason": "无indata权限"
}
```

---

## 六、异常检测规则

| 检测类型 | 规则 | 处理方式 |
| :--- | :--- | :--- |
| 请求频率异常 | 1小时内请求超过100次 | 加入黑名单 |
| 连续失败 | 失败次数超过5次 | 加入黑名单 |
| 异地登录 | 短时间内从5个以上不同IP访问 | 加入黑名单 |
| IP共享 | 同一IP被20个以上不同Agent使用 | 加入黑名单 |
| 委托链异常 | 委托链权限校验失败 | 拦截请求 |

---

## 七、日志存储格式

日志文件存储在 `IAMsystem/Logs/audit_trail_Log/` 目录下，按日期命名：`audit_YYYYMMDD.log`

日志格式为 JSON 单行格式，便于快速读取和解析：

```json
{"log_id": "uuid-xxx", "timestamp": 1745800000000, "agent_id": "DocAgent", "ip": "127.0.0.1", "operation": "authorize", "status": "success", "detail": {...}}
```