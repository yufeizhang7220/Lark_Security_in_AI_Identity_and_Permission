from fastapi import APIRouter, HTTPException
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

@router.post("/identity/register/user", status_code=201)
async def register_user(request: UserRegisterRequest):
    if Storage.find_user_by_name(request.Agent_name):
        audit_detail = {
            "subtype": request.subtype,
            "scope": request.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id="",
            ip=request.ip,
            status="fail",
            detail=audit_detail,
            agent_name=request.Agent_name
        )
        raise HTTPException(status_code=400, detail="Agent名称已存在")

    plain_secret = generate_agent_secret()
    hashed_secret = Storage.hash_secret(plain_secret)
    agent_id = generate_agent_id("user")

    user_data = {
        "agent_id": agent_id,
        "agent_name": request.Agent_name,
        "subtype": request.subtype,
        "agent_secret": hashed_secret,
        "scope": request.scope,
        "ip": request.ip,
        "registered_at": int(time.time()),
        "status": "active"
    }

    if not Storage.add_user(user_data):
        audit_detail = {
            "subtype": request.subtype,
            "scope": request.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=agent_id,
            ip=request.ip,
            status="fail",
            detail=audit_detail,
            agent_name=request.Agent_name
        )
        raise HTTPException(status_code=500, detail="服务器内部错误")

    audit_detail = {
        "subtype": request.subtype,
        "scope": request.scope,
        "agent_secret": "****"
    }
    AuditLogger.log_register(
        agent_id=agent_id,
        ip=request.ip,
        status="success",
        detail=audit_detail,
        agent_name=request.Agent_name
    )

    return {
        "code": 201,
        "message": "success",
        "data": {
            "Agent_name": request.Agent_name,
            "subtype": request.subtype,
            "scope": request.scope,
            "agent_id": agent_id,
            "agent_secret": plain_secret,
            "registered_at": int(time.time())
        }
    }

@router.post("/identity/register/bot", status_code=201)
async def register_bot(request: BotRegisterRequest):
    if Storage.find_bot_by_name(request.Bot_name):
        audit_detail = {
            "subtype": "bot",
            "scope": request.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=request.Bot_id or "",
            ip=request.ip,
            status="fail",
            detail=audit_detail,
            agent_name=request.Bot_name
        )
        raise HTTPException(status_code=400, detail="Bot名称已存在")

    bot_id = request.Bot_id or generate_agent_id("bot")
    plain_secret = generate_agent_secret()
    hashed_secret = Storage.hash_secret(plain_secret)

    bot_data = {
        "bot_id": bot_id,
        "bot_name": request.Bot_name,
        "agent_secret": hashed_secret,
        "scope": request.scope,
        "sub_scope": request.sub_scope or {"user": request.scope, "visitor": {}},
        "ip": request.ip,
        "api_endpoint": request.api_endpoint,
        "registered_at": int(time.time()),
        "status": "active"
    }

    if not Storage.add_bot(bot_data):
        audit_detail = {
            "subtype": "bot",
            "scope": request.scope,
            "agent_secret": "****"
        }
        AuditLogger.log_register(
            agent_id=bot_id,
            ip=request.ip,
            status="fail",
            detail=audit_detail,
            agent_name=request.Bot_name
        )
        raise HTTPException(status_code=500, detail="服务器内部错误")

    audit_detail = {
        "subtype": "bot",
        "scope": request.scope,
        "agent_secret": "****"
    }
    AuditLogger.log_register(
        agent_id=bot_id,
        ip=request.ip,
        status="success",
        detail=audit_detail,
        agent_name=request.Bot_name
    )

    return {
        "code": 201,
        "message": "success",
        "data": {
            "Agent_name": request.Bot_name,
            "subtype": "bot",
            "scope": request.scope,
            "agent_id": bot_id,
            "agent_secret": plain_secret,
            "registered_at": int(time.time())
        }
    }

@router.post("/identity/verify")
async def verify_identity(request: VerifyRequest):
    user = Storage.find_user_by_id(request.agent_id)
    if user:
        is_valid = Storage.verify_secret(request.agent_secret, user["agent_secret"])
        audit_detail = {
            "valid": is_valid,
            "scope": user.get("scope", {}) if is_valid else {}
        }
        AuditLogger.log_verify(
            agent_id=request.agent_id,
            ip="",
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

    bot = Storage.find_bot_by_id(request.agent_id)
    if bot:
        is_valid = Storage.verify_secret(request.agent_secret, bot["agent_secret"])
        audit_detail = {
            "valid": is_valid,
            "scope": bot.get("scope", {}) if is_valid else {}
        }
        AuditLogger.log_verify(
            agent_id=request.agent_id,
            ip="",
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

    audit_detail = {
        "valid": False,
        "fail_reason": "Agent不存在"
    }
    AuditLogger.log_verify(
        agent_id=request.agent_id,
        ip="",
        status="fail",
        detail=audit_detail
    )
    raise HTTPException(status_code=401, detail="身份验证失败")

@router.get("/health")
async def health_check():
    return {"code": 200, "message": "success", "data": {"status": "healthy"}}
