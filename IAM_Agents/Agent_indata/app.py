from fastapi import FastAPI, Path, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from datetime import datetime
import uuid
import uvicorn
from typing import Optional

from config import AGENT_ID, HOST, PORT, DEFAULT_BOT_SCOPE
from agent import AgentIndata
from utils import setup_logger, log_request, log_response, AGENT_CONFIG
from tools import TOOLS
from iam_client import iam_client

app = FastAPI(title="Agent_indata API", version="1.0")

# 启动时自动注册Bot
@app.on_event("startup")
async def startup_event():
    if not iam_client.register_bot():
        print("警告：Bot注册失败，将无法进行Token校验")

agent = AgentIndata()
logger = setup_logger("Agent_indata")

# Token校验依赖
async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少有效的Authorization头，格式为: Bearer {access_token}")
    
    access_token = authorization.split(" ")[1]
    # 当前query接口需要的权限
    required_scope = {"indata": ["read_contact", "read_calendar", "read_bitable"]}
    
    verify_result = iam_client.verify_access_token(access_token, required_scope)
    if not verify_result.get("valid", False):
        raise HTTPException(status_code=403, detail=verify_result.get("message", "权限不足"))
    
    return verify_result




class QueryRequest(BaseModel):
    Agent_id: str = AGENT_ID
    session_id: str = None
    session_datetime: str = None
    context: dict





@app.post(f"/{AGENT_ID}/api/query")
async def query(request: QueryRequest, token_info: dict = Depends(verify_token)):
    if request.session_id is None:
        request.session_id = str(uuid.uuid4())
    if request.session_datetime is None:
        request.session_datetime = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    log_request(logger, request.dict())

    # result = agent.process_request(request.context)

    response = {
        "Agent_id": request.Agent_id,
        "session_id": request.session_id,
        "session_datetime": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        "context": {
            "task_type": request.context.get("task_type", ""),
            "priority": request.context.get("priority", ""),
            "Agent_data": {
                "query_type": request.context.get("Agent_data", {}).get("query_type", ""),
                "output_type": request.context.get("Agent_data", {}).get("output_type", "json"),
                "query_data": {
                    "table":[{"姓名":"张三","成绩":"90","班级":"A班"},{"姓名":"李四","成绩":"85","班级":"A班"},{"姓名":"王五","成绩":"88","班级":"A班"}]
                }
            }
        }
    }

    log_response(logger, response)
    return response





@app.get(f"/{AGENT_ID}/health")
async def health():
    return {
        "status": "healthy",
        "service": AGENT_ID,
        "version": "1.0"
    }


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
