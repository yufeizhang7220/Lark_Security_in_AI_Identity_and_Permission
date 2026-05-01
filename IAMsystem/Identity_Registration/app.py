"""
身份注册 API 实现
"""

import secrets
import time
import os
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, status
from pydantic import BaseModel
from storage import Storage

router = APIRouter()

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs", "Identity_Registration_Log")
LOG_FILE = os.path.join(LOG_DIR, "registration.log")

os.makedirs(LOG_DIR, exist_ok=True)

file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(message)s'))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def generate_secret(length: int = 32) -> str:
    """生成随机密钥"""
    return secrets.token_hex(length // 2)


def get_current_timestamp() -> int:
    """获取当前时间戳（秒）"""
    return int(time.time())


def get_readable_time() -> str:
    """获取可读时间格式"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_registration(who: str, ip: str, identity: str, scope: Dict, extra_info: str, result_code: int, message: str):
    """
    记录注册日志，格式符合团队要求
    [时间] [谁] 在 [ip] 注册 [身份] 权限 [权限范围] [其他信息] 结果 [status] 原因 [message]
    """
    scope_str = str(scope).replace("'", '"')
    if extra_info:
        log_msg = f"[{get_readable_time()}] [{who}] 在 [{ip}] 注册 [{identity}] 权限 {scope_str} {extra_info} 结果 {result_code} 原因 {message}"
    else:
        log_msg = f"[{get_readable_time()}] [{who}] 在 [{ip}] 注册 [{identity}] 权限 {scope_str} 结果 {result_code} 原因 {message}"

    if result_code == 201:
        logger.info(log_msg)
    else:
        logger.error(log_msg)


class UserRegisterRequest(BaseModel):
    AgentID: str
    Subtype: str
    scope: Dict[str, List[str]]
    ip: str


class BotRegisterRequest(BaseModel):
    AgentID: str
    Subtype: str
    scope: Dict[str, List[str]]
    bot_description: str
    apis: List[Dict[str, Any]]
    ip: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(request: UserRegisterRequest):
    """
    用户注册
    写入 USERS_table.json
    """
    users = Storage.load_users()

    if request.AgentID in users:
        log_registration(
            who=request.AgentID,
            ip=request.ip,
            identity=request.Subtype,
            scope=request.scope,
            extra_info="",
            result_code=400,
            message="AgentID已存在"
        )
        return {
            "code": 400,
            "message": "AgentID已存在",
            "data": None
        }

    agent_secret = generate_secret()
    registered_at = get_current_timestamp()

    user_data = {
        "AgentID": request.AgentID,
        "Subtype": request.Subtype,
        "scope": request.scope,
        "AgentSecret": agent_secret,
        "registered_at": registered_at,
        "ip": request.ip
    }

    users[request.AgentID] = user_data

    if not Storage.save_users(users):
        log_registration(
            who=request.AgentID,
            ip=request.ip,
            identity=request.Subtype,
            scope=request.scope,
            extra_info="",
            result_code=500,
            message="文件写入失败"
        )
        return {
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }

    log_registration(
        who=request.AgentID,
        ip=request.ip,
        identity=request.Subtype,
        scope=request.scope,
        extra_info="",
        result_code=201,
        message="注册成功"
    )

    return {
        "code": 201,
        "message": "注册成功",
        "data": user_data
    }


@router.post("/register/bot", status_code=status.HTTP_201_CREATED)
def register_bot(request: BotRegisterRequest):
    """
    机器注册（Agent注册）
    写入 USERS_table.json 和 BOTS_table.json
    """
    users = Storage.load_users()

    if request.AgentID in users:
        log_registration(
            who=request.AgentID,
            ip=request.ip,
            identity=request.Subtype,
            scope=request.scope,
            extra_info=f"APIs数量:{len(request.apis)}",
            result_code=400,
            message="AgentID已存在"
        )
        return {
            "code": 400,
            "message": "AgentID已存在",
            "data": None
        }

    agent_secret = generate_secret()
    registered_at = get_current_timestamp()

    user_data = {
        "AgentID": request.AgentID,
        "Subtype": request.Subtype,
        "scope": request.scope,
        "AgentSecret": agent_secret,
        "registered_at": registered_at,
        "ip": request.ip
    }

    users[request.AgentID] = user_data
    if not Storage.save_users(users):
        log_registration(
            who=request.AgentID,
            ip=request.ip,
            identity=request.Subtype,
            scope=request.scope,
            extra_info=f"APIs数量:{len(request.apis)}",
            result_code=500,
            message="USERS_table写入失败"
        )
        return {
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }

    bots = Storage.load_bots()

    bot_data = {
        "bot_name": request.AgentID,
        "bot_description": request.bot_description,
        "API_adderess": []
    }

    for api in request.apis:
        api_entry = {
            "api_id": api.get("api_id"),
            "api": api.get("api"),
            "description": api.get("description", ""),
            "method": api.get("method"),
            "scope": api.get("scope", {}),
            "required_json": api.get("required_json", {}),
            "output_json": api.get("output_json", {})
        }
        bot_data["API_adderess"].append(api_entry)

    bots[request.AgentID] = bot_data

    if not Storage.save_bots(bots):
        log_registration(
            who=request.AgentID,
            ip=request.ip,
            identity=request.Subtype,
            scope=request.scope,
            extra_info=f"APIs数量:{len(request.apis)}",
            result_code=500,
            message="BOTS_table写入失败"
        )
        return {
            "code": 500,
            "message": "服务器内部错误",
            "data": None
        }

    log_registration(
        who=request.AgentID,
        ip=request.ip,
        identity=request.Subtype,
        scope=request.scope,
        extra_info=f"描述:{request.bot_description}, APIs数量:{len(request.apis)}",
        result_code=201,
        message="机器注册成功"
    )

    return {
        "code": 201,
        "message": "机器注册成功",
        "data": user_data
    }


@router.get("/bot/{AgentID}/api/{api_id}")
def get_bot_api(AgentID: str, api_id: str):
    """
    查询机器 API 信息（通过 api_id）
    """
    bots = Storage.load_bots()

    if AgentID not in bots:
        return {
            "code": 404,
            "message": "Agent 或 api_id 不存在",
            "data": None
        }

    bot = bots[AgentID]
    apis = bot.get("API_adderess", [])

    for api in apis:
        if api.get("api_id") == api_id:
            return {
                "code": 200,
                "data": api
            }

    return {
        "code": 404,
        "message": "Agent 或 api_id 不存在",
        "data": None
    }


@router.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Identity-Registration-API"
    }
