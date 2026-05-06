from fastapi import FastAPI, Path, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import uuid
import uvicorn

from config import AGENT_ID, HOST, PORT, DEFAULT_BOT_SCOPE
from agent import AgentIndata
from utils import setup_logger, log_request, log_response, register_bot, verify_identity, apply_access_token, verify_access_token, revoke_access_token, get_access_token, AGENT_CONFIG, load_local_reg_info, load_local_access_tokens
from tools import call_iam_tool, TOOLS

app = FastAPI(title="Agent_indata API", version="1.0")

async def verify_access_token_middleware(request: Request):
    auth_header = request.headers.get("Authorization")
    
    whitelist_paths = [
        f"/{AGENT_ID}/health",
        f"/{AGENT_ID}/iam/register",
        f"/{AGENT_ID}/iam/verify",
        f"/{AGENT_ID}/iam/apply-token",
        f"/{AGENT_ID}/iam/status",
        f"/{AGENT_ID}/iam/tools"
    ]
    
    if str(request.url.path) in whitelist_paths:
        return True
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": 401, "message": "缺少有效的Authorization头", "data": None})
    
    access_token = auth_header.replace("Bearer ", "").strip()
    
    if AGENT_CONFIG["AgentSecret"]:
        result = verify_access_token(
            bot_id=AGENT_CONFIG["AgentID"],
            agent_secret=AGENT_CONFIG["AgentSecret"],
            access_token=access_token,
            required_scope={"indata": ["read_contact", "read_calendar", "read_bitable"]}
        )
        
        if result.get("code") != 200 or not result.get("data", {}).get("valid"):
            raise HTTPException(status_code=403, detail={"code": 403, "message": "Token验证失败或权限不足", "data": None})
    
    return True

agent = AgentIndata()
logger = setup_logger("Agent_indata")

load_local_reg_info()
load_local_access_tokens()


class QueryRequest(BaseModel):
    Agent_id: str = AGENT_ID
    session_id: str = None
    session_datetime: str = None
    context: dict


class RegisterRequest(BaseModel):
    Bot_name: str = AGENT_ID
    scope: dict = None
    sub_scope: dict = None
    api_endpoint: str = None
    ip: str = "127.0.0.1"


class VerifyRequest(BaseModel):
    agent_id: str
    agent_secret: str


class ApplyTokenRequest(BaseModel):
    agent_id: str = AGENT_ID
    agent_secret: str = None
    applied_scope: dict = None
    purpose: str = "获取企业数据"
    ttl: int = 3600
    token_type: str = "dynamic"


class VerifyTokenRequest(BaseModel):
    bot_id: str
    agent_secret: str
    access_token: str
    required_scope: dict


class RevokeTokenRequest(BaseModel):
    agent_id: str = AGENT_ID
    agent_secret: str = None
    access_token: str
    revoke_reason: str = "主动撤销"


@app.post(f"/{AGENT_ID}/api/query")
async def query(request: QueryRequest, _: bool = Depends(verify_access_token_middleware)):
    if request.session_id is None:
        request.session_id = str(uuid.uuid4())
    if request.session_datetime is None:
        request.session_datetime = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    log_request(logger, request.dict())

    result = agent.process_request(request.context)

    response = {
        "Agent_id": request.Agent_id,
        "session_id": request.session_id,
        "session_datetime": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        "context": {
            "task_type": request.context.get("task_type", ""),
            "priority": request.context.get("priority", ""),
            "Agent_data": result
        }
    }

    log_response(logger, response)
    return response


@app.post(f"/{AGENT_ID}/iam/register")
async def iam_register(request: RegisterRequest):
    bot_name = request.Bot_name
    scope = request.scope if request.scope else DEFAULT_BOT_SCOPE
    sub_scope = request.sub_scope
    api_endpoint = request.api_endpoint
    ip = request.ip

    log_request(logger, {
        "endpoint": "/iam/register",
        "Bot_name": bot_name,
        "scope": scope,
        "sub_scope": sub_scope,
        "api_endpoint": api_endpoint,
        "ip": ip
    })

    result = register_bot(bot_name, scope, sub_scope, api_endpoint, ip)

    log_response(logger, result)
    return result


@app.post(f"/{AGENT_ID}/iam/verify")
async def iam_verify(request: VerifyRequest):
    log_request(logger, {
        "endpoint": "/iam/verify",
        "agent_id": request.agent_id,
        "agent_secret": "******"
    })

    result = verify_identity(request.agent_id, request.agent_secret)

    log_response(logger, result)
    return result


@app.get(f"/{AGENT_ID}/iam/status")
async def iam_status():
    result = call_iam_tool("get_registration_status", {})
    return result


@app.get(f"/{AGENT_ID}/iam/tools")
async def iam_tools():
    return {
        "code": 200,
        "message": "success",
        "data": TOOLS
    }


@app.post(f"/{AGENT_ID}/iam/apply-token")
async def iam_apply_token(request: ApplyTokenRequest):
    agent_id = request.agent_id
    agent_secret = request.agent_secret if request.agent_secret else AGENT_CONFIG["AgentSecret"]
    applied_scope = request.applied_scope if request.applied_scope else DEFAULT_BOT_SCOPE
    purpose = request.purpose
    ttl = request.ttl
    token_type = request.token_type

    log_request(logger, {
        "endpoint": "/iam/apply-token",
        "agent_id": agent_id,
        "agent_secret": "******",
        "applied_scope": applied_scope,
        "purpose": purpose,
        "ttl": ttl,
        "token_type": token_type
    })

    if not agent_secret:
        result = {"code": 401, "message": "请先完成身份注册", "data": None}
    else:
        result = apply_access_token(agent_id, agent_secret, applied_scope, purpose, ttl, token_type)

    log_response(logger, result)
    return result


@app.post(f"/{AGENT_ID}/iam/verify-token")
async def iam_verify_token(request: VerifyTokenRequest):
    log_request(logger, {
        "endpoint": "/iam/verify-token",
        "bot_id": request.bot_id,
        "agent_secret": "******",
        "access_token": "******",
        "required_scope": request.required_scope
    })

    result = verify_access_token(
        bot_id=request.bot_id,
        agent_secret=request.agent_secret,
        access_token=request.access_token,
        required_scope=request.required_scope
    )

    log_response(logger, result)
    return result


@app.post(f"/{AGENT_ID}/iam/revoke-token")
async def iam_revoke_token(request: RevokeTokenRequest):
    agent_id = request.agent_id
    agent_secret = request.agent_secret if request.agent_secret else AGENT_CONFIG["AgentSecret"]
    access_token = request.access_token
    revoke_reason = request.revoke_reason

    log_request(logger, {
        "endpoint": "/iam/revoke-token",
        "agent_id": agent_id,
        "agent_secret": "******",
        "access_token": "******",
        "revoke_reason": revoke_reason
    })

    if not agent_secret:
        result = {"code": 401, "message": "请先完成身份注册", "data": None}
    elif not access_token:
        result = {"code": 400, "message": "缺少access_token", "data": None}
    else:
        result = revoke_access_token(agent_id, agent_secret, access_token, revoke_reason)

    log_response(logger, result)
    return result


@app.get(f"/{AGENT_ID}/iam/get-token")
async def iam_get_token(force_refresh: bool = False):
    log_request(logger, {
        "endpoint": "/iam/get-token",
        "force_refresh": force_refresh
    })

    result = get_access_token(force_refresh)

    log_response(logger, result)
    return result


@app.get(f"/{AGENT_ID}/health")
async def health():
    return {
        "status": "healthy",
        "service": AGENT_ID,
        "version": "1.0",
        "registered": bool(AGENT_CONFIG["AgentSecret"]),
        "has_access_token": bool(AGENT_CONFIG["AccessToken"])
    }


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
