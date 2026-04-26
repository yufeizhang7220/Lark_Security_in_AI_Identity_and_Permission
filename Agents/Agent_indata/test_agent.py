import requests
from datetime import datetime
import uuid
import json
import logging
from pathlib import Path

BASE_URL = "http://localhost:8787"
AGENT_ID = "Agent_indata"

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("test_agent")
logger.setLevel(logging.INFO)
log_file = LOG_DIR / f"test_agent_{datetime.now().strftime('%Y%m%d')}.log"
handler = logging.FileHandler(log_file, encoding='utf-8')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


def log_response(test_name: str, response: requests.Response):
    try:
        data = response.json()
        logger.info(f"[{test_name}] Response: {json.dumps(data, ensure_ascii=False)}")
        print(f"[{test_name}] Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        logger.info(f"[{test_name}] Response: {response.text}")
        print(f"[{test_name}] Response: {response.text}")


def test_autonomous_query(query: str, description: str):
    payload = {
        "Agent_id": AGENT_ID,
        "session_id": str(uuid.uuid4()),
        "session_datetime": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
        "context": {
            "task_type": "autonomous",
            "priority": "user",
            "Agent_data": {
                "query_type": "",
                "output_type": "json",
                "query_data": query
            },
            "timeout": 60
        }
    }
    print(f"\n=== 测试: {description} ===")
    print(f"查询: {query}")
    response = requests.post(f"{BASE_URL}/{AGENT_ID}/api/query", json=payload)
    log_response(f"autonomous_{description}", response)
    return response


class TestAgentIndata:

    def test_health_check(self):
        response = requests.get(f"{BASE_URL}/{AGENT_ID}/health")
        log_response("test_health_check", response)

    def test_help(self):
        payload = {
            "Agent_id": AGENT_ID,
            "session_id": str(uuid.uuid4()),
            "session_datetime": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            "context": {
                "task_type": "help",
                "priority": "user",
                "Agent_data": {
                    "query_type": "",
                    "output_type": "json",
                    "query_data": ""
                },
                "timeout": 30
            }
        }
        response = requests.post(f"{BASE_URL}/{AGENT_ID}/api/query", json=payload)
        log_response("test_help", response)


if __name__ == "__main__":
    print("=== 开始测试 Agent_indata (自主版本) ===")

    test = TestAgentIndata()

    print("\n=== 测试自主分析能力 ===")

    test_autonomous_query("查询 学生成绩单", "搜索员工")

    print("\n=== 测试完成 ===")