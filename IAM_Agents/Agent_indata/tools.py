from utils import run_lark_command, register_bot, verify_identity, apply_access_token, verify_access_token, revoke_access_token, get_access_token, AGENT_CONFIG
from pathlib import Path
from config import DEFAULT_BOT_SCOPE
import json
import os
import httpx

SKILL_DOCS_DIR = Path(__file__).parent / "lark-doc"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "iam_register_bot",
            "description": "调用IAM系统身份注册API，以机器身份(bot)注册本Agent到IAM系统，获得agent_secret，是使用其他IAM API的前提。",
            "parameters": {
                "type": "object",
                "properties": {
                    "Bot_name": {"type": "string", "description": "Bot名称，默认值为Agent_indata"},
                    "scope": {"type": "object", "description": "申请的权限范围，格式为{\"资源类型\": [\"操作列表\"]}"},
                    "sub_scope": {"type": "object", "description": "不同身份的权限映射表，可选"},
                    "api_endpoint": {"type": "string", "description": "Bot服务地址，可选"},
                    "ip": {"type": "string", "description": "注册IP，默认127.0.0.1"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_verify_identity",
            "description": "调用IAM系统身份校验API，验证agent_id和agent_secret的合法性。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "系统生成的唯一ID"},
                    "agent_secret": {"type": "string", "description": "注册时返回的密钥"}
                },
                "required": ["agent_id", "agent_secret"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_apply_access_token",
            "description": "调用IAM系统委托授权API，申请AccessToken，用于访问其他需要权限的API。需要先完成身份注册后才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "已注册的AgentID，默认值为Agent_indata"},
                    "agent_secret": {"type": "string", "description": "注册时获得的AgentSecret"},
                    "applied_scope": {"type": "object", "description": "申请的权限范围，格式为{\"资源类型\": [\"操作列表\"]}"},
                    "purpose": {"type": "string", "description": "申请Token的用途，默认值为获取企业数据"},
                    "ttl": {"type": "integer", "description": "有效期，单位秒，最大86400，默认3600"},
                    "token_type": {"type": "string", "description": "Token类型：dynamic(动态)/static(静态)，默认dynamic"}
                },
                "required": ["agent_secret", "applied_scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_verify_access_token",
            "description": "调用IAM系统委托授权API，校验AccessToken的合法性和权限范围。供被调用的Agent使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "bot_id": {"type": "string", "description": "调用方Bot的唯一ID"},
                    "agent_secret": {"type": "string", "description": "调用方Bot的密钥"},
                    "access_token": {"type": "string", "description": "待校验的AccessToken"},
                    "required_scope": {"type": "object", "description": "当前接口需要的权限范围"}
                },
                "required": ["bot_id", "agent_secret", "access_token", "required_scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_revoke_access_token",
            "description": "调用IAM系统委托授权API，撤销已签发的AccessToken，使其立即失效。",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent唯一ID"},
                    "agent_secret": {"type": "string", "description": "Agent密钥"},
                    "access_token": {"type": "string", "description": "待撤销的完整AccessToken"},
                    "revoke_reason": {"type": "string", "description": "撤销原因，默认主动撤销"}
                },
                "required": ["agent_id", "agent_secret", "access_token"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_access_token",
            "description": "获取AccessToken，如果已有有效的缓存Token则直接返回，否则自动申请新的Token。",
            "parameters": {
                "type": "object",
                "properties": {
                    "force_refresh": {"type": "boolean", "description": "是否强制刷新Token，默认false"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_registration_status",
            "description": "获取当前Agent的注册状态和配置信息。",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]


def read_skill_file(relative_path: str) -> str:
    file_path = SKILL_DOCS_DIR / relative_path
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    return ""


def get_all_skill_docs() -> dict:
    docs = {}
    if SKILL_DOCS_DIR.exists():
        for root, dirs, files in os.walk(SKILL_DOCS_DIR):
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(SKILL_DOCS_DIR))
                    docs[rel_path] = read_skill_file(rel_path)
    return docs


def get_skill_summary() -> str:
    summary = """This agent can access Feishu/Lark OpenAPI through lark-cli tool.

Available lark-cli modules and commands (read SKILL.md for details):
- lark-doc: Cloud documents (docs +fetch, +create, +update, etc.)
- lark-drive: Cloud drive (drive +search)
- lark-contact: Contacts (contact +search-user, +get-user)
- lark-calendar: Calendar (calendar +agenda, calendars list)
- lark-base: Multi-dimensional tables (base +record-list, +table-list, etc.)
- lark-sheets: Spreadsheets
- lark-im: Instant messaging

IAM System Integration:
- iam_register_bot: Register as bot identity
- iam_verify_identity: Verify identity credentials
- get_registration_status: Check registration status

The agent should read the relevant SKILL.md files to understand command syntax and flags.
"""
    return summary


def execute_lark_command(command: list, as_user: bool = True) -> dict:
    if as_user and "--as" not in command:
        cmd = command + ["--as", "user"]
    else:
        cmd = command
    if "--format" not in cmd:
        cmd.extend(["--format", "json"])
    result = run_lark_command(cmd)
    return result


def call_iam_tool(tool_name: str, params: dict) -> dict:
    try:
        if tool_name == "iam_register_bot":
            bot_name = params.get("Bot_name", "Agent_indata")
            scope = params.get("scope", DEFAULT_BOT_SCOPE)
            sub_scope = params.get("sub_scope")
            api_endpoint = params.get("api_endpoint")
            ip = params.get("ip", "127.0.0.1")
            
            result = register_bot(bot_name, scope, sub_scope, api_endpoint, ip)
            return result
            
        elif tool_name == "iam_verify_identity":
            agent_id = params.get("agent_id")
            agent_secret = params.get("agent_secret")
            
            if not agent_id or not agent_secret:
                return {"code": 400, "message": "缺少agent_id或agent_secret", "data": None}
            
            result = verify_identity(agent_id, agent_secret)
            return result
            
        elif tool_name == "iam_apply_access_token":
            agent_id = params.get("agent_id", AGENT_CONFIG["AgentID"])
            agent_secret = params.get("agent_secret", AGENT_CONFIG["AgentSecret"])
            applied_scope = params.get("applied_scope", DEFAULT_BOT_SCOPE)
            purpose = params.get("purpose", "获取企业数据")
            ttl = params.get("ttl", 3600)
            token_type = params.get("token_type", "dynamic")
            
            if not agent_secret:
                return {"code": 400, "message": "缺少agent_secret，请先完成身份注册", "data": None}
            
            result = apply_access_token(agent_id, agent_secret, applied_scope, purpose, ttl, token_type)
            return result
            
        elif tool_name == "iam_verify_access_token":
            bot_id = params.get("bot_id")
            agent_secret = params.get("agent_secret")
            access_token = params.get("access_token")
            required_scope = params.get("required_scope")
            
            if not bot_id or not agent_secret or not access_token or not required_scope:
                return {"code": 400, "message": "缺少必要参数", "data": None}
            
            result = verify_access_token(bot_id, agent_secret, access_token, required_scope)
            return result
            
        elif tool_name == "iam_revoke_access_token":
            agent_id = params.get("agent_id", AGENT_CONFIG["AgentID"])
            agent_secret = params.get("agent_secret", AGENT_CONFIG["AgentSecret"])
            access_token = params.get("access_token")
            revoke_reason = params.get("revoke_reason", "主动撤销")
            
            if not agent_secret or not access_token:
                return {"code": 400, "message": "缺少agent_secret或access_token", "data": None}
            
            result = revoke_access_token(agent_id, agent_secret, access_token, revoke_reason)
            return result
            
        elif tool_name == "get_access_token":
            force_refresh = params.get("force_refresh", False)
            result = get_access_token(force_refresh)
            return result
            
        elif tool_name == "get_registration_status":
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "AgentID": AGENT_CONFIG["AgentID"],
                    "AgentSecret": "******" if AGENT_CONFIG["AgentSecret"] else "",
                    "AccessToken": "******" if AGENT_CONFIG["AccessToken"] else "",
                    "TokenExpire": AGENT_CONFIG["TokenExpire"],
                    "is_registered": bool(AGENT_CONFIG["AgentSecret"]),
                    "has_access_token": bool(AGENT_CONFIG["AccessToken"])
                }
            }
            
        else:
            return {"code": 400, "message": f"未知工具: {tool_name}", "data": None}
            
    except Exception as e:
        return {"code": 500, "message": f"工具调用失败: {str(e)}", "data": None}
