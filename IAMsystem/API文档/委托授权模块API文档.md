# 委托授权模块API文档

## 模块说明
本模块是IAM系统的核心授权服务，负责AccessToken的签发、校验、撤销，支持动态/静态两种Token类型，实现OAuth2.0客户端凭证模式的标准授权流程。

- 服务地址：`http://localhost:9001`
- 统一前缀：`/IAMsystem/auth`
- 内容类型：`application/json`
- 字符编码：`utf-8`

---

## 统一规范

### 1. 统一响应格式
所有接口的响应均遵循以下格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```
| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码，200表示成功，其他表示失败 |
| `message` | string | 结果描述，成功为"success"，失败为具体错误原因 |
| `data` | object | 业务数据，失败时为null |

### 2. 统一错误码对照表
| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| 200 | 请求成功 | 正常处理业务逻辑 |
| 400 | 请求参数错误 | 检查请求参数格式是否正确 |
| 401 | 身份验证失败 | 检查agent_id/agent_secret是否正确，Token是否过期/被篡改 |
| 403 | 权限不足 | 检查申请的权限是否超出Agent权限范围，或Token权限不足 |
| 404 | 资源不存在 | 检查请求的接口路径是否正确，或要撤销的Token是否存在 |
| 500 | 服务器内部错误 | 联系管理员排查服务端问题 |

### 3. Token使用规范
调用其他Agent接口时，需将AccessToken放到请求头中：
```http
Authorization: Bearer {AccessToken字符串}
```

---

## 接口列表

| 接口路径 | HTTP方法 | 功能描述 | 是否需要鉴权 |
|---------|---------|---------|-------------|
| `/apply-token` | POST | 申请AccessToken | 是（需传入agent_id和agent_secret） |
| `/verify-token` | POST | 校验AccessToken合法性 | 是（需传入调用方bot_id和agent_secret） |
| `/revoke-token` | POST | 撤销已签发的AccessToken | 是（需传入agent_id和agent_secret） |
| `/health` | GET | 健康检查接口 | 否 |

---

## 接口详情

### 1. 申请AccessToken
#### 接口说明
为Agent签发AccessToken，支持动态/静态两种Token类型，申请的权限为Agent自身权限与申请权限的交集。

#### 请求参数
```json
{
  "agent_id": "user_001",
  "agent_secret": "my_secure_password_123",
  "delegated_chain": [],
  "applied_scope": {"doc": ["write"], "indata": ["read_bitable"]},
  "purpose": "生成销售报告",
  "ttl": 3600,
  "token_type": "dynamic"
}
```
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | 是 | Agent唯一ID |
| `agent_secret` | string | 是 | Agent密钥 |
| `delegated_chain` | array | 否 | 委托链，代表用户委托调用时传入，默认为空数组 |
| `applied_scope` | object | 是 | 申请的权限范围，格式为"资源类型:操作列表" |
| `purpose` | string | 否 | Token用途，用于审计，默认为空 |
| `ttl` | int | 否 | Token有效期，单位秒，最长24小时(86400秒)，默认3600秒 |
| `token_type` | string | 否 | Token类型：`dynamic`(动态)/`static`(静态)，默认dynamic |

#### 响应示例
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
    "accesstoken_type": "dynamic",
    "expire_at": 1777865240,
    "granted_scope": {
      "doc": ["write"],
      "indata": ["read_bitable"]
    }
  }
}
```
| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string | JWT格式的AccessToken |
| `accesstoken_type` | string | Token类型：dynamic/static |
| `expire_at` | int | Token过期时间戳，静态Token为null |
| `granted_scope` | object | 实际授予的权限范围 |

#### curl调用示例
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/apply-token" \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "user_001",
  "agent_secret": "my_secure_password_123",
  "applied_scope": {"doc": ["write"], "indata": ["read_bitable"]},
  "purpose": "测试申请Token",
  "ttl": 3600,
  "token_type": "dynamic"
}'
```

---

### 2. 校验AccessToken
#### 接口说明
校验AccessToken是否合法，是否具备所需权限，供被调用的Agent使用。

#### 请求参数
```json
{
  "bot_id": "bot_data_001",
  "agent_secret": "bot_secure_password_123",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
  "required_scope": {"indata": ["read_bitable"]}
}
```
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `bot_id` | string | 是 | 调用方Bot的唯一ID |
| `agent_secret` | string | 是 | 调用方Bot的密钥 |
| `access_token` | string | 是 | 待校验的AccessToken |
| `required_scope` | object | 是 | 当前接口需要的权限范围 |

#### 响应示例
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "accesstoken_type": "dynamic",
    "scope": {
      "indata": ["read_bitable"]
    }
  }
}
```
| 字段 | 类型 | 说明 |
|------|------|------|
| `valid` | boolean | Token是否有效且具备所需权限 |
| `accesstoken_type` | string | Token类型 |
| `scope` | object | Token拥有的权限范围 |

#### curl调用示例
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/verify-token" \
-H "Content-Type: application/json" \
-d '{
  "bot_id": "bot_data_001",
  "agent_secret": "bot_secure_password_123",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
  "required_scope": {"indata": ["read_bitable"]}
}'
```

---

### 3. 撤销AccessToken
#### 接口说明
将已签发的AccessToken加入黑名单，使其立即失效。

#### 请求参数
```json
{
  "agent_id": "user_001",
  "agent_secret": "my_secure_password_123",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
  "revoke_reason": "主动撤销"
}
```
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | string | 是 | Agent唯一ID |
| `agent_secret` | string | 是 | Agent密钥 |
| `access_token` | string | 是 | 待撤销的完整AccessToken |
| `revoke_reason` | string | 否 | 撤销原因，默认"主动撤销" |
> 权限说明：**只有Token的申请者本人可以撤销自己的Token**，如果agent_id和Token中的AgentID不一致会返回403权限不足

#### 响应示例
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "revoked_at": 1777862659,
    "revoked_by": "user_001",
    "revoke_reason": "主动撤销"
  }
}
```
| 字段 | 类型 | 说明 |
|------|------|------|
| `valid` | boolean | 撤销是否成功 |
| `revoked_at` | int | 撤销时间戳 |
| `revoked_by` | string | 执行撤销操作的AgentID |
| `revoke_reason` | string | 撤销原因 |

#### curl调用示例
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/revoke-token" \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "user_001",
  "agent_secret": "my_secure_password_123",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
  "revoke_reason": "主动撤销"
}'
```

---

### 4. 健康检查接口
#### 接口说明
检查服务是否正常运行。

#### 请求示例
```bash
curl "http://localhost:9001/IAMsystem/auth/health"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "service": "delegated-authorization"
  }
}
```

---

## 附录

### 1. AccessToken(JWT)结构说明
解码后的Payload字段：
```json
{
  "iss": "IAM-System",
  "AgentID": "user_001",
  "iat": 1777862659,
  "jti": "40f99f914f534afa8b61383388875399",
  "delegated_chain": [],
  "scope": {
    "indata": ["read_bitable"]
  },
  "ip": "127.0.0.1",
  "purpose": "测试Token",
  "exp": 1777866259
}
```
| 字段 | 类型 | 说明 |
|------|------|------|
| `iss` | string | 签发者，固定为"IAM-System" |
| `AgentID` | string | Token所属的AgentID |
| `iat` | int | 签发时间戳 |
| `jti` | string | Token唯一标识 |
| `delegated_chain` | array | 委托链，记录调用链路 |
| `scope` | object | Token拥有的权限范围 |
| `ip` | string | 绑定的IP地址，"0.0.0.0"表示不受IP限制 |
| `purpose` | string | Token用途 |
| `exp` | int | 过期时间戳 |

### 2. 权限声明(scope)结构说明
采用"资源类型:操作列表"的键值对结构：
```json
{
  "doc": ["read", "write", "delete"],
  "indata": ["read_contact", "read_calendar", "read_bitable"],
  "online": ["web_search","fetch_content","analyze_content"],
  "iam": ["apply_token", "verify_token"]
}
```
预定义资源类型：
| 资源类型 | 说明 |
|---------|------|
| `doc` | 飞书文档操作权限 |
| `indata` | 企业内部数据访问权限 |
| `online` | 外部网络访问权限 |
| `iam` | IAM系统自身操作权限 |

### 3. Token类型说明
| 类型 | 说明 | 适用场景 |
|------|------|---------|
| `dynamic` | 动态Token | 默认类型，有有效期限制，绑定申请时的IP地址，安全性高 |
| `static` | 静态Token | 无过期时间，不受IP限制，仅用于可信的内部服务调用 |

### 4. 快速启动服务
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```
服务启动后访问`http://localhost:9001/docs`可以查看Swagger在线接口文档。
