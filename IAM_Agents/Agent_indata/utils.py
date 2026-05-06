import subprocess
import json
import logging
import time
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

LOG_DIR = Path(__file__).parent.parent.parent / "Agents/Agent_indata/logs"
LOG_DIR.mkdir(exist_ok=True)

project_root = Path(__file__).parent
REG_INFO_FILE = project_root / "Storage" / "IMA_reg_info.json"
ACCESS_TOKENS_FILE = project_root / "Storage" / "AccessTokens.json"

AGENT_CONFIG = {
    "AgentID": "Agent_indata",
    "AgentSecret": "",
    "AccessToken": "",
    "TokenExpire": 0
}


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def log_request(logger: logging.Logger, request_data: dict):
    logger.info(f"REQUEST: {json.dumps(request_data, ensure_ascii=False)}")


def log_response(logger: logging.Logger, response_data: dict):
    logger.info(f"RESPONSE: {json.dumps(response_data, ensure_ascii=False)}")


def log_lark_operation(logger: logging.Logger, operation: str, command: str, result: str):
    logger.info(f"LARK_OPERATION: {operation} | COMMAND: {command} | RESULT: {result}")


def run_lark_command(command: list, logger: logging.Logger = None) -> dict:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=False
        )
        output = result.stdout.strip() if result.stdout else result.stderr.strip()

        if logger:
            log_lark_operation(logger, command[1] + " " + command[2] if len(command) > 2 else str(command), " ".join(command), output[:500])

        if result.returncode != 0:
            return {"code": result.returncode, "msg": "error", "data": {"error": output}}

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"code": 0, "msg": "success", "data": {"raw_output": output}}

    except Exception as e:
        error_msg = str(e)
        if logger:
            logger.error(f"LARK_COMMAND_ERROR: {' '.join(command)} | ERROR: {error_msg}")
        return {"code": 1, "msg": "error", "data": {"error": error_msg}}


def load_local_reg_info() -> bool:
    try:
        if REG_INFO_FILE.exists():
            with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                reg_info = json.load(f)
                if AGENT_CONFIG["AgentID"] in reg_info:
                    agent_info = reg_info[AGENT_CONFIG["AgentID"]]
                    AGENT_CONFIG["AgentSecret"] = agent_info.get("agent_secret", "")
                    return True
    except Exception as e:
        print(f"Failed to load registration info: {e}")
    return False


def save_local_reg_info(agent_info: Dict) -> bool:
    try:
        reg_info = {}
        if REG_INFO_FILE.exists():
            with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                reg_info = json.load(f)
        
        reg_info[AGENT_CONFIG["AgentID"]] = agent_info
        with open(REG_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(reg_info, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Failed to save registration info: {e}")
        return False


def load_local_access_tokens() -> bool:
    try:
        current_time = int(time.time())
        if ACCESS_TOKENS_FILE.exists():
            with open(ACCESS_TOKENS_FILE, "r", encoding="utf-8") as f:
                tokens = json.load(f)
                for token_id, token_info in tokens.items():
                    if token_info.get("agent_id") == AGENT_CONFIG["AgentID"]:
                        if token_info.get("exp") == -1 or token_info.get("exp", 0) > current_time:
                            AGENT_CONFIG["AccessToken"] = token_info.get("agent_secret", "")
                            AGENT_CONFIG["TokenExpire"] = token_info.get("exp", 0)
                            return True
    except Exception as e:
        print(f"Failed to load access tokens: {e}")
    return False


def save_access_token(access_token: Dict) -> bool:
    try:
        tokens = {}
        if ACCESS_TOKENS_FILE.exists():
            with open(ACCESS_TOKENS_FILE, "r", encoding="utf-8") as f:
                tokens = json.load(f)
        
        current_time = int(time.time())
        expired_token_ids = []
        for token_id, token_info in tokens.items():
            if token_info.get("exp") != -1 and token_info.get("exp", 0) < current_time:
                expired_token_ids.append(token_id)
        
        for token_id in expired_token_ids:
            del tokens[token_id]
        
        token_id = access_token.get("token_id", f"tk_{int(time.time())}")
        access_token["token_id"] = token_id
        tokens[token_id] = access_token
        
        with open(ACCESS_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=4)
        
        AGENT_CONFIG["AccessToken"] = access_token.get("agent_secret", "")
        AGENT_CONFIG["TokenExpire"] = access_token.get("exp", 0)
        return True
    except Exception as e:
        print(f"Failed to save access token: {e}")
        return False


def register_bot(agent_name: str, scope: Dict, sub_scope: Dict = None, api_endpoint: str = None, ip: str = "127.0.0.1") -> Dict:
    from config import IAM_CONFIG
    
    try:
        register_data = {
            "Bot_name": agent_name,
            "scope": scope
        }
        
        if sub_scope:
            register_data["sub_scope"] = sub_scope
        if api_endpoint:
            register_data["api_endpoint"] = api_endpoint
        if ip:
            register_data["ip"] = ip
        
        response = httpx.post(
            IAM_CONFIG["identity_registration_url"],
            json=register_data,
            timeout=30
        )
        
        result = response.json()
        
        if result.get("code") == 201:
            agent_info = result["data"]
            AGENT_CONFIG["AgentSecret"] = agent_info["agent_secret"]
            
            save_local_reg_info({
                "agent_id": agent_info["agent_id"],
                "agent_name": agent_info["Agent_name"],
                "subtype": agent_info["subtype"],
                "scope": agent_info["scope"],
                "agent_secret": agent_info["agent_secret"],
                "registered_at": agent_info["registered_at"],
                "ip": ip
            })
            
            result["message"] = "注册成功，AgentSecret已保存"
        
        return result
    
    except Exception as e:
        return {"code": 500, "message": f"注册失败: {str(e)}", "data": None}


def verify_identity(agent_id: str, agent_secret: str) -> Dict:
    from config import IAM_CONFIG
    
    try:
        verify_data = {
            "agent_id": agent_id,
            "agent_secret": agent_secret
        }
        
        response = httpx.post(
            IAM_CONFIG["identity_verify_url"],
            json=verify_data,
            timeout=30
        )
        
        return response.json()
    
    except Exception as e:
        return {"code": 500, "message": f"验证失败: {str(e)}", "data": None}


def apply_access_token(agent_id: str, agent_secret: str, applied_scope: Dict, purpose: str = "", ttl: int = 3600, token_type: str = "dynamic", delegated_chain: list = None) -> Dict:
    from config import IAM_CONFIG
    
    try:
        request_data = {
            "agent_id": agent_id,
            "agent_secret": agent_secret,
            "applied_scope": applied_scope,
            "purpose": purpose,
            "ttl": ttl,
            "token_type": token_type,
            "delegated_chain": delegated_chain if delegated_chain else []
        }
        
        response = httpx.post(
            IAM_CONFIG["auth_apply_token_url"],
            json=request_data,
            timeout=30
        )
        
        result = response.json()
        
        if result.get("code") == 200 and result.get("data"):
            token_data = result["data"]
            save_access_token({
                "token_id": token_data.get("access_token", f"tk_{int(time.time())}"),
                "agent_id": agent_id,
                "agent_secret": token_data.get("access_token", ""),
                "scope": token_data.get("granted_scope", {}),
                "iat": int(time.time()),
                "exp": token_data.get("expire_at", 0),
                "IP": "127.0.0.1",
                "purpose": purpose
            })
        
        return result
    
    except Exception as e:
        return {"code": 500, "message": f"申请Token失败: {str(e)}", "data": None}


def verify_access_token(bot_id: str, agent_secret: str, access_token: str, required_scope: Dict) -> Dict:
    from config import IAM_CONFIG
    
    try:
        request_data = {
            "bot_id": bot_id,
            "agent_secret": agent_secret,
            "access_token": access_token,
            "required_scope": required_scope
        }
        
        response = httpx.post(
            IAM_CONFIG["auth_verify_token_url"],
            json=request_data,
            timeout=30
        )
        
        return response.json()
    
    except Exception as e:
        return {"code": 500, "message": f"验证Token失败: {str(e)}", "data": None}


def revoke_access_token(agent_id: str, agent_secret: str, access_token: str, revoke_reason: str = "主动撤销") -> Dict:
    from config import IAM_CONFIG
    
    try:
        request_data = {
            "agent_id": agent_id,
            "agent_secret": agent_secret,
            "access_token": access_token,
            "revoke_reason": revoke_reason
        }
        
        response = httpx.post(
            IAM_CONFIG["auth_revoke_token_url"],
            json=request_data,
            timeout=30
        )
        
        result = response.json()
        
        if result.get("code") == 200:
            AGENT_CONFIG["AccessToken"] = ""
            AGENT_CONFIG["TokenExpire"] = 0
        
        return result
    
    except Exception as e:
        return {"code": 500, "message": f"撤销Token失败: {str(e)}", "data": None}


def get_access_token(force_refresh: bool = False) -> Dict:
    if not AGENT_CONFIG["AgentSecret"]:
        return {"code": 401, "message": "请先完成身份注册", "data": None}
    
    current_time = int(time.time())
    
    if not force_refresh and AGENT_CONFIG["AccessToken"]:
        if AGENT_CONFIG["TokenExpire"] == -1 or AGENT_CONFIG["TokenExpire"] > current_time:
            return {
                "code": 200,
                "message": "success",
                "data": {
                    "access_token": AGENT_CONFIG["AccessToken"],
                    "expire_at": AGENT_CONFIG["TokenExpire"],
                    "status": "cached"
                }
            }
    
    from config import DEFAULT_BOT_SCOPE
    result = apply_access_token(
        agent_id=AGENT_CONFIG["AgentID"],
        agent_secret=AGENT_CONFIG["AgentSecret"],
        applied_scope=DEFAULT_BOT_SCOPE,
        purpose="获取企业数据",
        ttl=3600
    )
    
    return result


load_local_reg_info()
load_local_access_tokens()
