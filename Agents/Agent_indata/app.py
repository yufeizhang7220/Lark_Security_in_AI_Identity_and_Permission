from fastapi import FastAPI, Path
from pydantic import BaseModel
from datetime import datetime
import uuid
import uvicorn

from config import AGENT_ID, HOST, PORT
from agent import AgentIndata
from utils import setup_logger, log_request, log_response

app = FastAPI(title="Agent_indata API")

agent = AgentIndata()
logger = setup_logger("Agent_indata")


class QueryRequest(BaseModel):
    Agent_id: str = AGENT_ID
    session_id: str = None
    session_datetime: str = None
    context: dict


@app.post(f"/{AGENT_ID}/api/query")
async def query(request: QueryRequest):
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
        "service": AGENT_ID
    }


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)