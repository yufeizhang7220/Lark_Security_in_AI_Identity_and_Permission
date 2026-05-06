from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

app = FastAPI(title="IAM Admin API", version="1.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置路径
STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Storage")
LOGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logs")

# 辅助函数：读取JSON文件
def read_json_file(file_path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

# 辅助函数：写入JSON文件
def write_json_file(file_path: str, data: Dict[str, Any]) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入文件失败: {str(e)}")

# 辅助函数：读取日志文件
def read_log_file(file_path: str) -> str:
    try:
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")

@app.get("/IAMsystem/admin/health", summary="健康检查")
async def health_check():
    return {"code": 200, "message": "success", "data": {"status": "ok", "service": "iam-admin"}}

@app.get("/IAMsystem/admin/users", summary="获取所有用户列表")
async def get_users():
    users_file = os.path.join(STORAGE_PATH, "users.json")
    users_data = read_json_file(users_file)
    users = users_data.get("data", []) if isinstance(users_data, dict) else []
    return {"code": 200, "message": "success", "data": users}

@app.get("/IAMsystem/admin/bots", summary="获取所有机器Agent列表")
async def get_bots():
    bots_file = os.path.join(STORAGE_PATH, "bots.json")
    bots_data = read_json_file(bots_file)
    bots = bots_data.get("data", []) if isinstance(bots_data, dict) else []
    
    # 统一字段名，兼容bot_id/bot_name和agent_id/agent_name
    for bot in bots:
        if "bot_id" in bot and "agent_id" not in bot:
            bot["agent_id"] = bot["bot_id"]
        if "bot_name" in bot and "agent_name" not in bot:
            bot["agent_name"] = bot["bot_name"]
    
    return {"code": 200, "message": "success", "data": bots}

@app.get("/IAMsystem/admin/blacklist", summary="获取黑名单")
async def get_blacklist():
    blacklist_file = os.path.join(STORAGE_PATH, "blacklist.json")
    blacklist = read_json_file(blacklist_file)
    return {"code": 200, "message": "success", "data": blacklist}

@app.post("/IAMsystem/admin/blacklist/add", summary="添加到黑名单")
async def add_to_blacklist(agent_id: Optional[str] = None, ip: Optional[str] = None, user_id: Optional[str] = None):
    if not agent_id and not ip and not user_id:
        raise HTTPException(status_code=400, detail="至少需要提供一个参数: agent_id, ip, user_id")
    
    blacklist_file = os.path.join(STORAGE_PATH, "blacklist.json")
    blacklist = read_json_file(blacklist_file)
    
    # 初始化字段
    if "agents" not in blacklist:
        blacklist["agents"] = []
    if "ips" not in blacklist:
        blacklist["ips"] = []
    if "users" not in blacklist:
        blacklist["users"] = []
    
    # 添加到对应列表
    if agent_id and agent_id not in blacklist["agents"]:
        blacklist["agents"].append(agent_id)
    if ip and ip not in blacklist["ips"]:
        blacklist["ips"].append(ip)
    if user_id and user_id not in blacklist["users"]:
        blacklist["users"].append(user_id)
    
    write_json_file(blacklist_file, blacklist)
    return {"code": 200, "message": "已加入黑名单"}

@app.post("/IAMsystem/admin/blacklist/remove", summary="从黑名单移除")
async def remove_from_blacklist(agent_id: Optional[str] = None, ip: Optional[str] = None, user_id: Optional[str] = None):
    if not agent_id and not ip and not user_id:
        raise HTTPException(status_code=400, detail="至少需要提供一个参数: agent_id, ip, user_id")
    
    blacklist_file = os.path.join(STORAGE_PATH, "blacklist.json")
    blacklist = read_json_file(blacklist_file)
    
    # 移除对应项
    if agent_id and "agents" in blacklist and agent_id in blacklist["agents"]:
        blacklist["agents"].remove(agent_id)
    if ip and "ips" in blacklist and ip in blacklist["ips"]:
        blacklist["ips"].remove(ip)
    if user_id and "users" in blacklist and user_id in blacklist["users"]:
        blacklist["users"].remove(user_id)
    
    write_json_file(blacklist_file, blacklist)
    return {"code": 200, "message": "已从黑名单移除"}

@app.get("/IAMsystem/admin/logs", summary="获取指定日期的所有日志")
async def get_logs(date: str):
    # date格式: YYYYMMDD
    if len(date) != 8:
        raise HTTPException(status_code=400, detail="日期格式错误，应为YYYYMMDD")
    
    log_files = [
        ("audit", os.path.join(LOGS_PATH, "audit_trail_log", f"audit_{date}.log")),
        ("registration", os.path.join(LOGS_PATH, "Identity_Registration_Log", f"registration_{date}.log")),
        ("apply_token", os.path.join(LOGS_PATH, "Delegated_Authorization_Log", "Apply_Token", f"apply_token_{date}.log")),
        ("verify_token", os.path.join(LOGS_PATH, "Delegated_Authorization_Log", "Verify_Token", f"verify_token_{date}.log")),
        ("revoke_token", os.path.join(LOGS_PATH, "Delegated_Authorization_Log", "Revoke_Token", f"revoke_token_{date}.log"))
    ]
    
    result = {}
    for log_type, file_path in log_files:
        if os.path.exists(file_path):
            result[log_type] = read_log_file(file_path)
        else:
            result[log_type] = ""
    
    return {"code": 200, "message": "success", "data": result}

@app.get("/IAMsystem/admin/anomalies", summary="获取最近N天的违规记录")
async def get_anomalies(days: int = 7):
    anomalies = []
    today = datetime.now()
    
    for i in range(days):
        date_str = (today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)).strftime("%Y%m%d")
        audit_log_path = os.path.join(LOGS_PATH, "audit_trail_log", f"audit_{date_str}.log")
        
        if not os.path.exists(audit_log_path):
            continue
            
        log_content = read_log_file(audit_log_path)
        for line in log_content.strip().split("\n"):
            if not line:
                continue
            try:
                # 日志格式: "时间 - 级别 - JSON内容"，需要先提取JSON部分
                if " - " in line:
                    json_part = line.split(" - ", 2)[2]
                    log_entry = json.loads(json_part)
                    if log_entry.get("status") in ["blocked", "fail"]:
                        anomalies.append(log_entry)
            except Exception as e:
                print(f"解析日志失败: {str(e)}, 行内容: {line[:100]}...")
                continue
    
    # 按时间倒序排序
    anomalies.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return {"code": 200, "message": "success", "data": anomalies}

@app.get("/IAMsystem/admin/stats", summary="获取统计数据")
async def get_stats():
    users_data = read_json_file(os.path.join(STORAGE_PATH, "users.json"))
    bots_data = read_json_file(os.path.join(STORAGE_PATH, "bots.json"))
    blacklist = read_json_file(os.path.join(STORAGE_PATH, "blacklist.json"))
    
    users = users_data.get("data", []) if isinstance(users_data, dict) else []
    bots = bots_data.get("data", []) if isinstance(bots_data, dict) else []
    
    total_users = len(users)
    total_bots = len(bots)
    blacklist_count = 0
    if isinstance(blacklist, dict):
        blacklist_count = len(blacklist.get("agents", [])) + len(blacklist.get("ips", [])) + len(blacklist.get("users", []))
    
    # 最近注册记录
    recent_registrations = []
    all_agents = []
    for user in users:
        user["subtype"] = "user"
        all_agents.append(user)
    for bot in bots:
        bot["subtype"] = "bot"
        all_agents.append(bot)
    
    all_agents.sort(key=lambda x: x.get("registered_at", 0), reverse=True)
    recent_registrations = all_agents[:5]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_users": total_users,
            "total_bots": total_bots,
            "blacklist_count": blacklist_count,
            "recent_registrations": recent_registrations
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9005)
