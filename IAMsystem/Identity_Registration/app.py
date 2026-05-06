from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Optional, Any
import time
import uuid
import secrets
from storage import Storage
from audit_logger import AuditLogger

router = APIRouter()

class UserRegisterRequest(BaseModel):
    Agent_name: str
    subtype: str
    scope: Dict[str, Any]
    ip: Optional[str] = "127.0.0.1"

class BotRegisterRequest(BaseModel):
    Bot_name: str
    Bot_id: Optional[str] = None
    scope: Dict[str, Any]
    ip: Optional[str] = "127.0.0.1"
    sub_scope: Optional[Dict[str, Dict[str, Any]]] = None
    api_endpoint: Optional[str] = ""

class VerifyRequest(BaseModel):
    agent_id: str
    agent_secret: str

def generate_agent_secret() -> str:
    return secrets.token_hex(16)

def generate_agent_id(prefix: str = "user") -> str:
    timestamp = int(time.time())
    random_str = secrets.token_hex(4)
    return f"{prefix}_{timestamp}_{random_str}"

@router.post("/register/user", status_code=201)
async def register_user(request: Request, req: UserRegisterRequest):
    client_ip = request.client.host
    # 全局黑名单校验
    if Storage.is_in_blacklist(ip=client_ip):
        audit_detail = {
            "subtype": req.subtype,
            "scope": req.scope,
            "fail_reason": "IP已被拉黑，禁止注册"
        }
        AuditLogger.log_register(
            agent_id="",
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Agent_name
        )
        raise HTTPException(status_code=403, detail="该IP已被拉黑，禁止操作")
    # 调用审计接口校验操作合法性
    audit_check_detail = {
        "subtype": req.subtype,
        "scope": req.scope,
        "ip": client_ip
    }
    if not AuditLogger.call_audit_api(agent_id="", operation="register", detail=audit_check_detail):
        raise HTTPException(status_code=403, detail="审计校验不通过，操作被拦截")
    if Storage.find_user_by_name(req.Agent_name):
        audit_detail = {
            "subtype": req.subtype,
            "scope": req.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id="",
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Agent_name
        )
        raise HTTPException(status_code=400, detail="Agent名称已存在")
    plain_secret = generate_agent_secret()
    hashed_secret = Storage.hash_secret(plain_secret)
    agent_id = generate_agent_id("user")
    # visitor身份只能拥有online相关权限，过滤其他权限
    user_scope = req.scope
    if req.subtype == "visitor":
        user_scope = {}
        if "online" in req.scope:
            user_scope["online"] = req.scope["online"]
    user_data = {
        "agent_id": agent_id,
        "agent_name": req.Agent_name,
        "subtype": req.subtype,
        "agent_secret": hashed_secret,
        "scope": user_scope,
        "ip": req.ip,
        "registered_at": int(time.time()),
        "status": "active"
    }
    if not Storage.add_user(user_data):
        audit_detail = {
            "subtype": req.subtype,
            "scope": req.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=agent_id,
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Agent_name
        )
        raise HTTPException(status_code=500, detail="服务器内部错误")
    audit_detail = {
        "subtype": req.subtype,
        "scope": req.scope,
        "agent_secret": "****"
    }
    AuditLogger.log_register(
        agent_id=agent_id,
        ip=client_ip,
        status="success",
        detail=audit_detail,
        agent_name=req.Agent_name
    )
    return {
        "code": 201,
        "message": "success",
        "data": {
            "Agent_name": req.Agent_name,
            "subtype": req.subtype,
            "scope": user_scope,
            "agent_id": agent_id,
            "agent_secret": plain_secret,
            "registered_at": int(time.time())
        }
    }

@router.post("/register/bot", status_code=201)
async def register_bot(request: Request, req: BotRegisterRequest):
    client_ip = request.client.host
    # 全局黑名单校验
    if Storage.is_in_blacklist(ip=client_ip):
        audit_detail = {
            "subtype": "bot",
            "scope": req.scope,
            "fail_reason": "IP已被拉黑，禁止注册"
        }
        AuditLogger.log_register(
            agent_id=req.Bot_id or "",
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Bot_name
        )
        raise HTTPException(status_code=403, detail="该IP已被拉黑，禁止操作")
    # 调用审计接口校验操作合法性
    audit_check_detail = {
        "subtype": "bot",
        "scope": req.scope,
        "ip": client_ip
    }
    if not AuditLogger.call_audit_api(agent_id="", operation="register", detail=audit_check_detail):
        raise HTTPException(status_code=403, detail="审计校验不通过，操作被拦截")
    if Storage.find_bot_by_name(req.Bot_name):
        audit_detail = {
            "subtype": "bot",
            "scope": req.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=req.Bot_id or "",
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Bot_name
        )
        raise HTTPException(status_code=400, detail="Bot名称已存在")
    bot_id = req.Bot_id or generate_agent_id("bot")
    plain_secret = generate_agent_secret()
    hashed_secret = Storage.hash_secret(plain_secret)
    # 处理sub_scope中的visitor权限，只能拥有online相关权限
    sub_scope = req.sub_scope or {"user": req.scope, "visitor": {}}
    if "visitor" in sub_scope:
        visitor_scope = sub_scope["visitor"]
        filtered_visitor_scope = {}
        if "online" in visitor_scope:
            filtered_visitor_scope["online"] = visitor_scope["online"]
        sub_scope["visitor"] = filtered_visitor_scope
    bot_data = {
        "bot_id": bot_id,
        "bot_name": req.Bot_name,
        "agent_secret": hashed_secret,
        "scope": req.scope,
        "sub_scope": sub_scope,
        "ip": req.ip,
        "api_endpoint": req.api_endpoint,
        "registered_at": int(time.time()),
        "status": "active"
    }
    if not Storage.add_bot(bot_data):
        audit_detail = {
            "subtype": "bot",
            "scope": req.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=bot_id,
            ip=client_ip,
            status="fail",
            detail=audit_detail,
            agent_name=req.Bot_name
        )
        raise HTTPException(status_code=500, detail="服务器内部错误")
    audit_detail = {
        "subtype": "bot",
        "scope": req.scope,
        "agent_secret": "****"
    }
    AuditLogger.log_register(
        agent_id=bot_id,
        ip=client_ip,
        status="success",
        detail=audit_detail,
        agent_name=req.Bot_name
    )
    return {
        "code": 201,
        "message": "success",
        "data": {
            "Agent_name": req.Bot_name,
            "subtype": "bot",
            "scope": req.scope,
            "agent_id": bot_id,
            "agent_secret": plain_secret,
            "registered_at": int(time.time())
        }
    }

@router.post("/verify")
async def verify_identity(request: Request, req: VerifyRequest):
    client_ip = request.client.host
    # 全局黑名单校验
    if Storage.is_in_blacklist(agent_id=req.agent_id, ip=client_ip):
        audit_detail = {
            "valid": False,
            "fail_reason": "Agent/IP已被拉黑，禁止操作"
        }
        AuditLogger.log_verify(
            agent_id=req.agent_id,
            ip=client_ip,
            status="fail",
            detail=audit_detail
        )
        raise HTTPException(status_code=403, detail="该Agent/IP已被拉黑，禁止操作")
    # 调用审计接口校验操作合法性
    audit_check_detail = {
        "ip": client_ip
    }
    if not AuditLogger.call_audit_api(agent_id=req.agent_id, operation="verify", detail=audit_check_detail):
        raise HTTPException(status_code=403, detail="审计校验不通过，操作被拦截")
    user = Storage.find_user_by_id(req.agent_id)
    if user:
        is_valid = Storage.verify_secret(req.agent_secret, user["agent_secret"])
        audit_detail = {
            "valid": is_valid,
            "scope": user.get("scope", {}) if is_valid else {}
        }
        AuditLogger.log_verify(
            agent_id=req.agent_id,
            ip=client_ip,
            status="success" if is_valid else "fail",
            detail=audit_detail
        )
        if is_valid:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "valid": True,
                    "scope": user["scope"]
                }
            }
        # 密码错误直接返回，不再查找Bot
        raise HTTPException(status_code=401, detail="身份验证失败")

    bot = Storage.find_bot_by_id(req.agent_id)
    if bot:
        is_valid = Storage.verify_secret(req.agent_secret, bot["agent_secret"])
        audit_detail = {
            "valid": is_valid,
            "scope": bot.get("scope", {}) if is_valid else {}
        }
        AuditLogger.log_verify(
            agent_id=req.agent_id,
            ip=client_ip,
            status="success" if is_valid else "fail",
            detail=audit_detail
        )
        if is_valid:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "valid": True,
                    "scope": bot["scope"]
                }
            }
        # 密码错误直接返回
        raise HTTPException(status_code=401, detail="身份验证失败")

    audit_detail = {
        "valid": False,
        "fail_reason": "Agent不存在"
    }
    AuditLogger.log_verify(
        agent_id=req.agent_id,
        ip=client_ip,
        status="fail",
        detail=audit_detail
    )
    raise HTTPException(status_code=401, detail="身份验证失败")

@router.get("/health")
async def health_check():
    return {"code": 200, "message": "success", "data": {"status": "healthy"}}
