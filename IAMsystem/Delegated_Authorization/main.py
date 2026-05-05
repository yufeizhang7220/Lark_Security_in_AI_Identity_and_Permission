"""
委托授权模块主服务
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import time
from config import SERVER_HOST, SERVER_PORT, API_PREFIX
from utils import (
    get_agent_by_id, verify_agent_secret, calculate_scope_intersection,
    generate_jwt, decode_jwt, is_token_in_blacklist, add_token_to_blacklist,
    check_scope_sufficient, call_audit_api, write_audit_log
)

app = FastAPI(title="IAM委托授权服务", description="Agent身份与权限系统-委托授权模块")

# ------------------------------ 请求参数模型 ------------------------------
class ApplyTokenRequest(BaseModel):
    agent_id: str = Field(..., description="Agent唯一ID")
    agent_secret: str = Field(..., description="Agent密钥")
    delegated_chain: List[Dict] = Field(default=[], description="委托链")
    applied_scope: Dict = Field(..., description="申请的权限范围")
    purpose: str = Field(default="", description="Token用途")
    ttl: int = Field(default=3600, description="Token有效期，单位秒，最长24小时")
    token_type: str = Field(default="dynamic", description="Token类型：dynamic(动态)/static(静态)")

class VerifyTokenRequest(BaseModel):
    bot_id: str = Field(..., description="调用方BotID")
    agent_secret: str = Field(..., description="调用方Bot密钥")
    access_token: str = Field(..., description="待校验的AccessToken")
    required_scope: Dict = Field(..., description="需要的权限范围")

class RevokeTokenRequest(BaseModel):
    agent_id: str = Field(..., description="Agent唯一ID")
    agent_secret: str = Field(..., description="Agent密钥")
    access_token: str = Field(..., description="待撤销的AccessToken")
    revoke_reason: str = Field(default="主动撤销", description="撤销原因")

# ------------------------------ 统一响应格式 ------------------------------
def success_response(data: Dict = None):
    return {
        "code": 200,
        "message": "success",
        "data": data or {}
    }

def error_response(code: int, message: str):
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "message": message,
            "data": None
        }
    )

# ------------------------------ 核心接口实现 ------------------------------
@app.post(f"{API_PREFIX}/apply-token", summary="申请AccessToken")
async def apply_token(request: Request, req: ApplyTokenRequest):
    """
    申请AccessToken接口，支持动态/静态两种类型
    """
    client_ip = request.client.host
    log_data = {
        "agent_id": req.agent_id,
        "applied_scope": req.applied_scope,
        "purpose": req.purpose,
        "ttl": req.ttl,
        "token_type": req.token_type,
        "ip": client_ip,
        "status": "fail",
        "fail_reason": ""
    }
    
    try:
        # 1. 验证Agent身份是否存在且状态正常
        agent = get_agent_by_id(req.agent_id)
        if not agent:
            log_data["fail_reason"] = "Agent不存在或已被禁用"
            write_audit_log("apply_token", log_data)
            return error_response(401, "Agent不存在或已被禁用")
        
        # 2. 验证Agent密钥是否正确
        if not verify_agent_secret(req.agent_secret, agent.get("agent_secret", "")):
            log_data["fail_reason"] = "Agent密钥错误"
            write_audit_log("apply_token", log_data)
            return error_response(401, "Agent密钥错误")
        
        # 3. 计算权限交集：Agent自身权限 ∩ 申请权限
        agent_scope = agent.get("scope", {})
        granted_scope = calculate_scope_intersection([agent_scope, req.applied_scope])
        
        # 4. 如果有委托链，还要和委托链中所有上层权限取交集
        if req.delegated_chain:
            chain_scopes = [item.get("scope", {}) for item in req.delegated_chain]
            granted_scope = calculate_scope_intersection([granted_scope] + chain_scopes)
        
        if not granted_scope:
            log_data["fail_reason"] = "申请的权限超出Agent权限范围"
            write_audit_log("apply_token", log_data)
            return error_response(403, "申请的权限超出Agent权限范围")
        
        # 5. 调用审计接口校验
        audit_data = {
            "agent_id": req.agent_id,
            "operation": "authorize",
            "detail": {
                "applied_scope": req.applied_scope,
                "granted_scope": granted_scope,
                "purpose": req.purpose
            }
        }
        if not call_audit_api(audit_data):
            log_data["fail_reason"] = "审计校验不通过"
            write_audit_log("apply_token", log_data)
            return error_response(403, "审计校验不通过")
        
        # 6. 生成JWT Token
        access_token, expire_at, jti = generate_jwt(
            agent_id=req.agent_id,
            scope=granted_scope,
            delegated_chain=req.delegated_chain,
            ip=client_ip,
            purpose=req.purpose,
            ttl=req.ttl,
            token_type=req.token_type
        )
        
        # 7. 写成功日志
        log_data.update({
            "status": "success",
            "jti": jti,
            "granted_scope": granted_scope,
            "expire_at": expire_at
        })
        write_audit_log("apply_token", log_data)
        
        # 8. 返回结果
        return success_response({
            "access_token": access_token,
            "accesstoken_type": req.token_type,
            "expire_at": expire_at,
            "granted_scope": granted_scope
        })
    
    except HTTPException as e:
        # 业务异常直接返回，已提前写入日志
        raise e
    except Exception as e:
        log_data["fail_reason"] = f"服务器内部错误: {str(e)}"
        write_audit_log("apply_token", log_data)
        return error_response(500, "服务器内部错误")

@app.post(f"{API_PREFIX}/verify-token", summary="校验AccessToken合法性")
async def verify_token(request: Request, req: VerifyTokenRequest):
    """
    校验AccessToken是否合法且具备所需权限
    """
    client_ip = request.client.host
    log_data = {
        "bot_id": req.bot_id,
        "required_scope": req.required_scope,
        "ip": client_ip,
        "status": "fail",
        "fail_reason": "",
        "valid": False
    }
    
    try:
        # 1. 校验调用方Bot身份和密钥
        bot_agent = get_agent_by_id(req.bot_id)
        if not bot_agent or bot_agent.get("type") != "bot":
            log_data["fail_reason"] = "调用方Bot不存在或已被禁用"
            write_audit_log("verify_token", log_data)
            return error_response(401, "调用方Bot不存在或已被禁用")
        
        if not verify_agent_secret(req.agent_secret, bot_agent.get("agent_secret", "")):
            log_data["fail_reason"] = "调用方Bot密钥错误"
            write_audit_log("verify_token", log_data)
            return error_response(401, "调用方Bot密钥错误")
        
        # 2. 解析AccessToken
        payload = decode_jwt(req.access_token)
        if not payload:
            log_data["fail_reason"] = "AccessToken无效或已过期"
            write_audit_log("verify_token", log_data)
            return error_response(401, "AccessToken无效或已过期")
        
        # 3. 检查Token是否在黑名单
        jti = payload.get("jti")
        if is_token_in_blacklist(jti):
            log_data["fail_reason"] = "AccessToken已被撤销"
            write_audit_log("verify_token", log_data)
            return error_response(401, "AccessToken已被撤销")
        
        # 4. 校验IP是否匹配（动态Token才校验）
        token_ip = payload.get("ip", "0.0.0.0")
        if token_ip != "0.0.0.0" and token_ip != client_ip:
            log_data["fail_reason"] = "IP地址不匹配"
            write_audit_log("verify_token", log_data)
            return error_response(403, "IP地址不匹配")
        
        # 5. 校验权限是否满足
        granted_scope = payload.get("scope", {})
        if not check_scope_sufficient(granted_scope, req.required_scope):
            log_data["fail_reason"] = "权限不足，无法访问该资源"
            write_audit_log("verify_token", log_data)
            return error_response(403, "权限不足，无法访问该资源")
        
        # 6. 调用审计接口校验
        audit_data = {
            "agent_id": payload.get("AgentID"),
            "operation": "verify",
            "detail": {
                "required_scope": req.required_scope,
                "granted_scope": granted_scope,
                "token_jti": jti
            }
        }
        if not call_audit_api(audit_data):
            log_data["fail_reason"] = "审计校验不通过"
            write_audit_log("verify_token", log_data)
            return error_response(403, "审计校验不通过")
        
        # 7. 写成功日志
        log_data.update({
            "status": "success",
            "valid": True,
            "agent_id": payload.get("AgentID"),
            "jti": jti,
            "granted_scope": granted_scope
        })
        write_audit_log("verify_token", log_data)
        
        # 8. 返回结果
        return success_response({
            "valid": True,
            "accesstoken_type": "static" if payload.get("ip") == "0.0.0.0" else "dynamic",
            "scope": granted_scope
        })
    
    except HTTPException as e:
        # 业务异常直接返回，已提前写入日志
        raise e
    except Exception as e:
        log_data["fail_reason"] = f"服务器内部错误: {str(e)}"
        write_audit_log("verify_token", log_data)
        return error_response(500, "服务器内部错误")

@app.post(f"{API_PREFIX}/revoke-token", summary="撤销AccessToken")
async def revoke_token(request: Request, req: RevokeTokenRequest):
    """
    撤销已签发的AccessToken，加入黑名单
    只有Token的申请者本人可以撤销自己的Token
    """
    client_ip = request.client.host
    log_data = {
        "agent_id": req.agent_id,
        "jti": "",
        "revoke_reason": req.revoke_reason,
        "ip": client_ip,
        "status": "fail",
        "fail_reason": ""
    }
    
    try:
        # 1. 验证Agent身份和密钥
        agent = get_agent_by_id(req.agent_id)
        if not agent:
            log_data["fail_reason"] = "Agent不存在或已被禁用"
            write_audit_log("revoke_token", log_data)
            return error_response(401, "Agent不存在或已被禁用")
        
        if not verify_agent_secret(req.agent_secret, agent.get("agent_secret", "")):
            log_data["fail_reason"] = "Agent密钥错误"
            write_audit_log("revoke_token", log_data)
            return error_response(401, "Agent密钥错误")
        
        # 2. 解析待撤销的AccessToken，验证合法性
        payload = decode_jwt(req.access_token)
        if not payload:
            log_data["fail_reason"] = "AccessToken无效或已过期"
            write_audit_log("revoke_token", log_data)
            return error_response(401, "AccessToken无效或已过期")
        
        jti = payload.get("jti")
        token_agent_id = payload.get("AgentID")
        log_data["jti"] = jti
        
        # 3. 校验只有Token的申请者可以撤销自己的Token
        if token_agent_id != req.agent_id:
            log_data["fail_reason"] = "权限不足，只能撤销自己申请的Token"
            write_audit_log("revoke_token", log_data)
            return error_response(403, "权限不足，只能撤销自己申请的Token")
        
        # 4. 检查Token是否已经被撤销
        if is_token_in_blacklist(jti):
            log_data["fail_reason"] = "Token已被撤销"
            write_audit_log("revoke_token", log_data)
            return error_response(400, "Token已被撤销")
        
        # 5. 调用审计接口校验
        audit_data = {
            "agent_id": req.agent_id,
            "operation": "authorize",
            "detail": {
                "jti": jti,
                "revoke_reason": req.revoke_reason
            }
        }
        if not call_audit_api(audit_data):
            log_data["fail_reason"] = "审计校验不通过"
            write_audit_log("revoke_token", log_data)
            return error_response(403, "审计校验不通过")
        
        # 6. 将Token加入黑名单（使用Token自身的过期时间，没有则默认保留24小时）
        expire_at = payload.get("exp", int(time.time()) + 86400)
        if not add_token_to_blacklist(jti, expire_at, req.agent_id, req.revoke_reason):
            log_data["fail_reason"] = "撤销失败，Token不存在"
            write_audit_log("revoke_token", log_data)
            return error_response(404, "撤销失败，Token不存在")
        
        # 7. 写成功日志
        log_data.update({
            "status": "success",
            "revoked_at": int(time.time()),
            "revoked_by": req.agent_id,
            "token_agent_id": token_agent_id
        })
        write_audit_log("revoke_token", log_data)
        
        # 8. 返回结果
        return success_response({
            "valid": True,
            "revoked_at": int(time.time()),
            "revoked_by": req.agent_id,
            "jti": jti,
            "revoke_reason": req.revoke_reason
        })
    
    except Exception as e:
        log_data["fail_reason"] = f"服务器内部错误: {str(e)}"
        write_audit_log("revoke_token", log_data)
        return error_response(500, "服务器内部错误")

@app.get(f"{API_PREFIX}/health", summary="健康检查接口")
async def health():
    return success_response({"status": "ok", "service": "delegated-authorization"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
