"""
外部检索 Agent API 服务
提供 FastAPI 接口支持
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Any, Dict
import uvicorn
import logging
import os

from external_search import ExternalSearchAgent

AGENT_ID = "External-Search-Agent"
HOST = "0.0.0.0"
PORT = 8787

app = FastAPI(title="External Search Agent API")

agent = ExternalSearchAgent()

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(LOGS_DIR, "external_search_agent.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("外部检索Agent")

logger.info(f"外部检索Agent API 服务初始化")
logger.info(f"Agent ID: {AGENT_ID}")


class QueryRequest(BaseModel):
    Agent_id: str = ""
    session_id: str = ""
    session_datetime: str = ""
    context: Dict[str, Any]


@app.post(f"/{AGENT_ID}/api/query")
async def query(request: QueryRequest):
    logger.info(f"接收请求: {request}")
    logger.info(f"Agent_id: {request.Agent_id}")
    logger.info(f"session_id: {request.session_id}")
    logger.info(f"session_datetime: {request.session_datetime}")
    logger.info(f"context: {request.context}")

    try:
        result = agent.execute_task({
            "context": request.context
        })
        logger.info(f"执行结果: {result}")
        return result
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        return {
            "success": False,
            "error_code": "SYS_001",
            "error_message": f"系统内部错误: {str(e)}"
        }


@app.get(f"/{AGENT_ID}/health")
async def health():
    logger.info("健康检查请求")
    return {
        "status": "healthy",
        "service": AGENT_ID
    }


@app.get("/health")
async def root_health():
    logger.info("根路径健康检查请求")
    return {
        "status": "healthy",
        "service": AGENT_ID
    }


if __name__ == "__main__":
    logger.info(f"启动外部检索Agent API 服务...")
    logger.info(f"API 地址: http://{HOST}:{PORT}/{AGENT_ID}/api/query")
    logger.info(f"健康检查: http://{HOST}:{PORT}/{AGENT_ID}/health")

    uvicorn.run(app, host=HOST, port=PORT)