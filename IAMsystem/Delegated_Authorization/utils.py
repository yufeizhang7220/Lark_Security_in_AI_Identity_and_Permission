"""
委托授权模块工具类
"""
import json
import os
import time
import uuid
import jwt
import bcrypt
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from config import (
    JWT_SECRET, JWT_ALGORITHM, MAX_TOKEN_TTL,
    USERS_JSON_PATH, BOTS_JSON_PATH, TOKEN_BLACKLIST_PATH, BLACKLIST_PATH,
    APPLY_TOKEN_LOG_DIR, VERIFY_TOKEN_LOG_DIR, REVOKE_TOKEN_LOG_DIR,
    AUDIT_API_URL
)

# ------------------------------ 存储操作工具 ------------------------------
# 读取JSON文件
def read_json_file(file_path: str) -> Dict:
    """读取JSON文件"""
    if not os.path.exists(file_path):
        return {"data": []}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"data": []}
# 读取全局黑名单
def read_global_blacklist() -> Dict:
    """读取全局黑名单文件"""
    if not os.path.exists(BLACKLIST_PATH):
        return {"agents": [], "ips": [], "users": []}
    try:
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"agents": [], "ips": [], "users": []}
# 检查是否在全局黑名单中
def is_in_blacklist(agent_id: str = "", ip: str = "") -> bool:
    """检查AgentID/用户ID/IP是否在全局黑名单中"""
    blacklist = read_global_blacklist()
    # 检查Agent/用户黑名单
    if agent_id:
        if agent_id in blacklist.get("agents", []) or agent_id in blacklist.get("users", []):
            return True
    # 检查IP黑名单
    if ip:
        if ip in blacklist.get("ips", []):
            return True
    return False

# 写入JSON文件
def write_json_file(file_path: str, data: Dict) -> bool:
    """写入JSON文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# 根据agent_id查询用户或Bot信息
def get_agent_by_id(agent_id: str) -> Optional[Dict]:
    """根据agent_id查询用户或Bot信息"""
    # 先查用户表
    users_data = read_json_file(USERS_JSON_PATH)
    for user in users_data.get("data", []):
        if user.get("agent_id") == agent_id and user.get("status") == "active":
            return {**user, "type": "user"}
    
    # 再查Bot表
    bots_data = read_json_file(BOTS_JSON_PATH)
    for bot in bots_data.get("data", []):
        if bot.get("bot_id") == agent_id and bot.get("status") == "active":
            return {**bot, "type": "bot", "agent_id": bot.get("bot_id")}
    
    return None

# 验证agent_secret是否正确
def verify_agent_secret(plain_secret: str, hashed_secret: str) -> bool:
    """验证agent_secret是否正确"""
    try:
        return bcrypt.checkpw(plain_secret.encode("utf-8"), hashed_secret.encode("utf-8"))
    except Exception:
        return False

# ------------------------------ 权限计算工具 ------------------------------
# 计算多个权限集合的交集，遵循最小权限原则
def calculate_scope_intersection(scopes: List[Dict]) -> Dict:
    """计算多个权限集合的交集，遵循最小权限原则"""
    if not scopes:
        return {}
    
    # 取第一个scope的所有资源类型作为基准
    result = {}
    base_scope = scopes[0]
    
    for resource_type, base_perms in base_scope.items():
        # 检查所有scope中都包含该资源类型
        all_has_resource = all(resource_type in scope for scope in scopes)
        if not all_has_resource:
            continue
        
        # 计算该资源类型下权限的交集
        perms_set = set(base_perms)
        for scope in scopes[1:]:
            perms_set.intersection_update(scope.get(resource_type, []))
        
        if perms_set:
            result[resource_type] = list(perms_set)
    
    return result

# 检查已授予的权限是否满足所需权限
def check_scope_sufficient(granted_scope: Dict, required_scope: Dict) -> bool:
    """检查已授予的权限是否满足所需权限"""
    for resource_type, required_perms in required_scope.items():
        # 如果资源类型不存在，直接不满足
        if resource_type not in granted_scope:
            return False
        
        granted_perms = set(granted_scope[resource_type])
        # 如果有all权限，直接满足
        if "all" in granted_perms:
            return True
        # 检查所有需要的权限都在已授予列表中
        for perm in required_perms:
            if perm not in granted_perms:
                return False
    
    return True

# ------------------------------ JWT工具 ------------------------------
# 生成JWT格式的AccessToken
def generate_jwt(
    agent_id: str,
    scope: Dict,
    delegated_chain: List[Dict],
    ip: str,
    purpose: str,
    ttl: int,
    token_type: str = "dynamic"
) -> Tuple[str, int, str]:
    """生成JWT格式的AccessToken"""
    jti = str(uuid.uuid4()).replace("-", "")
    now = int(time.time())
    
    payload = {
        "iss": "IAM-System",
        "AgentID": agent_id,
        "iat": now,
        "jti": jti,
        "delegated_chain": delegated_chain,
        "scope": scope,
        "ip": ip if token_type == "dynamic" else "0.0.0.0",
        "purpose": purpose
    }
    
    # 动态Token设置过期时间，静态Token不设置过期时间
    if token_type == "dynamic":
        ttl = min(ttl, MAX_TOKEN_TTL)
        exp = now + ttl
        payload["exp"] = exp
    else:
        exp = None
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, exp, jti

# 解析并验证JWT，验证失败返回None
def decode_jwt(token: str) -> Optional[Dict]:
    """解析并验证JWT，验证失败返回None"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": True})
        return payload
    except jwt.ExpiredSignatureError:
        # Token过期
        return None
    except Exception:
        # 签名错误或其他验证失败
        return None

# 检查Token是否在黑名单中
def is_token_in_blacklist(jti: str) -> bool:
    """检查Token是否在黑名单中"""
    blacklist_data = read_json_file(TOKEN_BLACKLIST_PATH)
    now = int(time.time())
    
    for item in blacklist_data.get("data", []):
        if item.get("jti") == jti:
            # 检查是否已过期，过期的黑名单条目自动忽略
            expire_at = item.get("expire_at")
            if expire_at is None or expire_at > now:
                return True
    
    return False

# 将Token加入黑名单
def add_token_to_blacklist(jti: str, expire_at: int, revoked_by: str, revoke_reason: str) -> bool:
    """将Token加入黑名单"""
    blacklist_data = read_json_file(TOKEN_BLACKLIST_PATH)
    now = int(time.time())
    
    # 检查是否已经在黑名单
    for item in blacklist_data.get("data", []):
        if item.get("jti") == jti:
            return False
    
    blacklist_data["data"].append({
        "jti": jti,
        "expire_at": expire_at,
        "revoked_at": now,
        "revoked_by": revoked_by,
        "revoke_reason": revoke_reason
    })
    
    return write_json_file(TOKEN_BLACKLIST_PATH, blacklist_data)

# ------------------------------ 日志工具 ------------------------------
# 写入审计日志，按天分片存储
def write_audit_log(log_type: str, log_data: Dict):
    """写入审计日志，按天分片存储"""
    today = datetime.now().strftime("%Y%m%d")
    log_file_name = f"{log_type}_{today}.log"
    
    if log_type == "apply_token":
        log_dir = APPLY_TOKEN_LOG_DIR
        # 上报到审计模块
        audit_data = {
            "agent_id": log_data.get("agent_id", ""),
            "ip": log_data.get("ip", ""),
            "token_id": log_data.get("jti", ""),
            "applied_scope": log_data.get("applied_scope", {}),
            "granted_scope": log_data.get("granted_scope", {}),
            "expire_at": log_data.get("expire_at", 0),
            "status": log_data.get("status", "success"),
            "fail_reason": log_data.get("fail_reason", "")
        }
        report_audit_log(AUDIT_AUTHORIZATION_URL, audit_data)
    elif log_type == "verify_token":
        log_dir = VERIFY_TOKEN_LOG_DIR
        # 上报到审计模块
        audit_data = {
            "agent_id": log_data.get("agent_id", ""),
            "ip": log_data.get("ip", ""),
            "token_id": log_data.get("jti", ""),
            "required_scope": log_data.get("required_scope", {}),
            "valid": log_data.get("valid", False),
            "fail_reason": log_data.get("fail_reason", "")
        }
        report_audit_log(AUDIT_VERIFICATION_URL, audit_data)
    elif log_type == "revoke_token":
        log_dir = REVOKE_TOKEN_LOG_DIR
        # 上报到审计模块
        audit_data = {
            "agent_id": log_data.get("agent_id", ""),
            "ip": log_data.get("ip", ""),
            "token_id": log_data.get("jti", ""),
            "applied_scope": {},
            "granted_scope": {},
            "expire_at": 0,
            "status": log_data.get("status", "success"),
            "fail_reason": log_data.get("fail_reason", "")
        }
        report_audit_log(AUDIT_AUTHORIZATION_URL, audit_data)
    else:
        return
    
    log_path = os.path.join(log_dir, log_file_name)
    log_entry = {
        "timestamp": int(time.time()),
        "log_id": str(uuid.uuid4()).replace("-", ""),
        **log_data
    }
    
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

# ------------------------------ 审计工具 ------------------------------
# 审计模块上报接口地址
AUDIT_RECORD_URL = "http://localhost:9000/IAMsystem/audit/record"
AUDIT_AUTHORIZATION_URL = "http://localhost:9000/IAMsystem/audit/record/authorization"
AUDIT_VERIFICATION_URL = "http://localhost:9000/IAMsystem/audit/record/verification"

def report_audit_log(url: str, data: Dict[str, Any]) -> bool:
    """上报日志到审计模块"""
    try:
        requests.post(url, json=data, timeout=2)
        return True
    except Exception:
        return False  # 上报失败不影响业务

# 调用审计接口检查操作是否合法
def call_audit_api(audit_data: Dict) -> bool:
    """调用审计接口检查操作是否合法"""
    try:
        now = int(time.time())
        # 补全审计接口要求的必填参数
        request_data = {
            "agent_id": audit_data.get("agent_id", ""),
            "start_time": now - 3600,  # 检查最近1小时的操作
            "end_time": now,
            "operation": audit_data.get("operation", ""),
            "detail": audit_data.get("detail", {})
        }
        response = requests.post(AUDIT_API_URL, json=request_data, timeout=3)
        if response.status_code == 200:
            result = response.json()
            return result.get("valid", False)
        return True  # 审计接口不可用时默认放行，保证可用性
    except Exception:
        return True  # 审计接口异常时默认放行
