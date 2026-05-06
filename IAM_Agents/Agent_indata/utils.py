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

AGENT_CONFIG = {
    "AgentID": "Agent_indata"
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



