from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import json
import time
import uuid
import os
from datetime import datetime

app = FastAPI(title="IAM Delegated Authorization API", version="1.0")

# 配置
AUTH_MODE = "dynamic"  # 可切换为 "static" 或 "dynamic"
PORT = 9000
MAX_TOKEN_EXPIRE = 86400  # 最大有效期24小时

# 文件路径
USERS_TABLE_PATH = "../Storage/USERS_table.json"
TOKENS_TABLE_PATH = "../Storage/TOKENS_table.json"
LOG_FILE_PATH = "../Logs/Delegated_Authorization_Log/AccessToken_Auth.log"

# 确保日志目录存在
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

# 请求模型
class AuthRequest(BaseModel):
    AgentID: str = Field(description="Agent的英文名")
    Subtype: str = Field(description="身份权限 user/visitor/bot")
    AgentSecret: str = Field(description="注册密钥")
    purpose: str = Field(description="申请目的")
    scope: Dict[str, List[str]] = Field(description="权限范围，格式为dict(str, list(str))")
    time: int = Field(description="希望使用时长，单位秒")

# 响应模型
class AuthResponse(BaseModel):
    AgentID: str
    status: int
    AccessToken: Dict = Field(default_factory=dict)

# 辅助函数
def load_json(file_path: str) -> Dict:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(file_path: str, data: Dict) -> None:
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def write_log(log_entry: str) -> None:
    """写入日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {log_entry}\n"
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_line)

def generate_secret() -> str:
    """生成新的AgentSecret"""
    return uuid.uuid4().hex + uuid.uuid4().hex[:8]

def generate_token_id() -> str:
    """生成唯一的TokenID"""
    return "tk_" + uuid.uuid4().hex

def validate_scope(requested_scopes: Dict[str, List[str]], user_scopes: Dict) -> bool:
    """验证请求的权限是否合法"""
    for data_type, operations in requested_scopes.items():
        # 检查数据类型是否在用户权限中（支持用户表中定义的任意数据类型：doc/tablebase/calendar/online等）
        if data_type not in user_scopes:
            return False
        
        # 检查用户是否有该操作权限，或者有all权限
        user_ops = user_scopes[data_type]
        if "all" in user_ops:
            continue
        
        # 检查每个请求的操作是否都在用户权限中
        for op in operations:
            if op not in user_ops:
                return False
    
    return True

@app.post("/IAMsystem/Delegated_Authorization", response_model=AuthResponse)
async def delegated_authorization(request: AuthRequest, req: Request):
    """委托授权API，分发AccessToken"""
    try:
        # 加载用户表
        users = load_json(USERS_TABLE_PATH)
        
        # 步骤1：验证用户是否存在
        if request.AgentID not in users:
            scope_str = json.dumps(request.scope, ensure_ascii=False)
            log_entry = f"[{request.AgentID}] [{request.Subtype}] 在 [{req.client.host}] 申请 [{scope_str}] 有效期到 [无效] 目的是 [{request.purpose}] 结果是 [602] 原因是 [用户未注册]"
            write_log(log_entry)
            return AuthResponse(
                AgentID=request.AgentID,
                status=602,
                AccessToken={}
            )
        
        user = users[request.AgentID]
        
        # 验证Subtype和AgentSecret是否匹配
        if user["Subtype"] != request.Subtype or user["AgentSecret"] != request.AgentSecret:
            scope_str = json.dumps(request.scope, ensure_ascii=False)
            log_entry = f"[{request.AgentID}] [{request.Subtype}] 在 [{req.client.host}] 申请 [{scope_str}] 有效期到 [无效] 目的是 [{request.purpose}] 结果是 [602] 原因是 [用户未注册/密钥错误]"
            write_log(log_entry)
            return AuthResponse(
                AgentID=request.AgentID,
                status=602,
                AccessToken={}
            )
        
        # 步骤2：验证权限是否合法
        if not validate_scope(request.scope, user["scope"]):
            scope_str = json.dumps(request.scope, ensure_ascii=False)
            log_entry = f"[{request.AgentID}] [{request.Subtype}] 在 [{req.client.host}] 申请 [{scope_str}] 有效期到 [无效] 目的是 [{request.purpose}] 结果是 [603] 原因是 [权限不足]"
            write_log(log_entry)
            return AuthResponse(
                AgentID=request.AgentID,
                status=603,
                AccessToken={}
            )
        
        # 步骤3：处理有效期
        requested_time = min(request.time, MAX_TOKEN_EXPIRE)
        current_time = int(time.time())
        
        # 生成新的密钥和TokenID
        new_secret = generate_secret()
        token_id = generate_token_id()
        
        # 处理IP和过期时间
        if AUTH_MODE == "static":
            ip = "0.0.0.0"
            exp = -1
            expire_str = "永久有效"
        else:  # dynamic
            ip = req.client.host
            exp = current_time + requested_time
            expire_str = datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S")
        
        # 组装AccessToken
        access_token = {
            "token_id": token_id,
            "AgentID": request.AgentID,
            "Subtype": request.Subtype,
            "scope": request.scope,
            "AgentSecret": new_secret,
            "iat": current_time,
            "exp": exp,
            "IP": ip,
            "purpose": request.purpose
        }
        
        # 保存到TOKENS表，以token_id作为key
        tokens = load_json(TOKENS_TABLE_PATH)
        tokens[token_id] = access_token
        save_json(TOKENS_TABLE_PATH, tokens)
        
        # 记录成功日志
        scope_str = json.dumps(request.scope, ensure_ascii=False)
        log_entry = f"[{request.AgentID}] [{request.Subtype}] 在 [{ip}] 申请 [{scope_str}] 有效期到 [{expire_str}] 目的是 [{request.purpose}] TokenID [{token_id}] 结果是 [601] 原因是 [正确通过]"
        write_log(log_entry)
        
        # 返回成功响应
        return AuthResponse(
            AgentID=request.AgentID,
            status=601,
            AccessToken=access_token
        )
    
    except Exception as e:
        # 处理未知错误
        try:
            scope_str = json.dumps(request.scope, ensure_ascii=False)
        except:
            scope_str = "无效格式"
        log_entry = f"[{request.AgentID}] [{request.Subtype}] 在 [{req.client.host}] 申请 [{scope_str}] 有效期到 [无效] 目的是 [{request.purpose}] 结果是 [604] 原因是 [未知错误: {str(e)}]"
        write_log(log_entry)
        return AuthResponse(
            AgentID=request.AgentID,
            status=604,
            AccessToken={}
        )

@app.get("/IAMsystem/Delegated_Authorization/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "Delegated-Authorization-API", "mode": AUTH_MODE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
