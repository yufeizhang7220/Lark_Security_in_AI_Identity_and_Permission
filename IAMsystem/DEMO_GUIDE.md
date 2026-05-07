# IAMsystem 演示脚本

## 前置条件
1. 已按照INSTALL_GUIDE.md完成依赖安装
2. 已启动所有IAM服务（执行python start_all.py）
3. 所有服务健康检查正常

---

## 演示场景1：用户身份注册与校验
### 步骤1：注册普通用户
**操作指令**：
```bash
curl -X POST http://localhost:9002/IAMsystem/identity/register/user \
-H "Content-Type: application/json" \
-d '{
  "Agent_name": "test_user_001",
  "subtype": "user",
  "scope": {
    "document": ["read", "write"],
    "chat": true,
    "online": true
  },
  "ip": "127.0.0.1"
}'
```

**预期结果**：
```json
{
  "code": 201,
  "message": "success",
  "data": {
    "Agent_name": "test_user_001",
    "subtype": "user",
    "scope": {"document": ["read","write"], "chat": true, "online": true},
    "agent_id": "user_xxxxxxxx_xxxxxx",
    "agent_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "registered_at": 17xxxxxxxxx
  }
}
```
> 请保存返回的`agent_id`和`agent_secret`，后续步骤需要使用

---

### 步骤2：身份校验
**操作指令**（将`your_agent_id`和`your_agent_secret`替换为上一步返回的值）：
```bash
curl -X POST http://localhost:9002/IAMsystem/identity/verify \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "your_agent_id",
  "agent_secret": "your_agent_secret"
}'
```

**预期结果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "scope": {"document": ["read","write"], "chat": true, "online": true}
  }
}
```

---

## 演示场景2：Access Token申请与校验
### 步骤1：申请动态Token
**操作指令**：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/apply-token \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "your_agent_id",
  "agent_secret": "your_agent_secret",
  "delegated_chain": [],
  "applied_scope": {
    "document": ["read"],
    "online": true
  },
  "purpose": "演示测试",
  "ttl": 3600,
  "token_type": "dynamic"
}'
```

**预期结果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxx.xxxxxx",
    "accesstoken_type": "dynamic",
    "expire_at": 17xxxxxxxxx,
    "granted_scope": {"document": ["read"], "online": true}
  }
}
```
> 注意：返回的`granted_scope`是申请权限与用户自身权限的交集，符合最小权限原则

---

### 步骤2：校验Token合法性（模拟Bot服务校验请求）
首先注册一个测试Bot：
```bash
curl -X POST http://localhost:9002/IAMsystem/identity/register/bot \
-H "Content-Type: application/json" \
-d '{
  "Bot_name": "test_bot_001",
  "scope": {
    "document": ["read", "write"],
    "chat": true
  }
}'
```
保存返回的Bot的`agent_id`和`agent_secret`。

然后校验Token：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/verify-token \
-H "Content-Type: application/json" \
-d '{
  "bot_id": "your_bot_id",
  "agent_secret": "your_bot_secret",
  "access_token": "your_access_token",
  "required_scope": {
    "document": ["read"]
  }
}'
```

**预期结果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "accesstoken_type": "dynamic",
    "scope": {"document": ["read"], "online": true}
  }
}
```

---

### 步骤3：校验权限不足场景
**操作指令**：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/verify-token \
-H "Content-Type: application/json" \
-d '{
  "bot_id": "your_bot_id",
  "agent_secret": "your_bot_secret",
  "access_token": "your_access_token",
  "required_scope": {
    "document": ["write"]
  }
}'
```

**预期结果**：
```json
{
  "code": 403,
  "message": "权限不足，缺失权限: {\"document\": [\"write\"]}",
  "data": null
}
```

---

## 演示场景3：Token撤销
**操作指令**：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/revoke-token \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "your_agent_id",
  "agent_secret": "your_agent_secret",
  "access_token": "your_access_token",
  "revoke_reason": "测试撤销"
}'
```

**预期结果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "valid": true,
    "revoked_at": 17xxxxxxxxx,
    "revoked_by": "your_agent_id",
    "jti": "xxxxxx",
    "revoke_reason": "测试撤销"
  }
}
```

撤销后再次校验该Token：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/verify-token \
-H "Content-Type: application/json" \
-d '{
  "bot_id": "your_bot_id",
  "agent_secret": "your_bot_secret",
  "access_token": "your_access_token",
  "required_scope": {
    "document": ["read"]
  }
}'
```

**预期结果**：
```json
{
  "code": 401,
  "message": "AccessToken已被撤销",
  "data": null
}
```

---

## 演示场景4：访客身份权限限制
### 步骤1：注册访客用户
**操作指令**：
```bash
curl -X POST http://localhost:9002/IAMsystem/identity/register/user \
-H "Content-Type: application/json" \
-d '{
  "Agent_name": "test_visitor_001",
  "subtype": "visitor",
  "scope": {
    "document": ["read", "write"],
    "chat": true,
    "online": true
  },
  "ip": "127.0.0.1"
}'
```

**预期结果**：
```json
{
  "code": 201,
  "message": "success",
  "data": {
    "Agent_name": "test_visitor_001",
    "subtype": "visitor",
    "scope": {"online": true},
    "agent_id": "user_xxxxxxxx_xxxxxx",
    "agent_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "registered_at": 17xxxxxxxxx
  }
}
```
> 注意：返回的`scope`仅保留了`online`权限，其他权限被自动过滤，符合访客权限限制规则

---

## 演示场景5：静态Token使用（适合服务间调用）
### 步骤1：申请静态Token
**操作指令**：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/apply-token \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "your_agent_id",
  "agent_secret": "your_agent_secret",
  "delegated_chain": [],
  "applied_scope": {
    "document": ["read"]
  },
  "purpose": "服务间调用",
  "ttl": 86400,
  "token_type": "static"
}'
```

**预期结果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxx.xxxxxx",
    "accesstoken_type": "static",
    "expire_at": 17xxxxxxxxx,
    "granted_scope": {"document": ["read"]}
  }
}
```

### 步骤2：静态Token不校验IP
使用不同IP（或模拟其他IP）校验，依然通过：
```bash
curl -X POST http://localhost:9001/IAMsystem/auth/verify-token \
-H "Content-Type: application/json" \
-H "X-Forwarded-For: 192.168.1.100" \
-d '{
  "bot_id": "your_bot_id",
  "agent_secret": "your_bot_secret",
  "access_token": "your_static_token",
  "required_scope": {
    "document": ["read"]
  }
}'
```

**预期结果**：返回`valid: true`，静态Token不受IP限制。

---

## 演示场景6：审计日志查看
所有操作都会被记录审计日志，日志文件存储在`Logs`目录下：
- 身份注册日志：`Logs/Identity_Registration_Log/registration_YYYYMMDD.log`
- Token申请日志：`Logs/Delegated_Authorization_Log/Apply_Token/apply_token_YYYYMMDD.log`
- Token校验日志：`Logs/Delegated_Authorization_Log/Verify_Token/verify_token_YYYYMMDD.log`
- 审计日志：`Logs/audit_trail_log/audit_YYYYMMDD.log`

也可以通过管理后台界面（http://localhost:9006）可视化查看所有审计记录和异常行为。
