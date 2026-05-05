import os
import uuid
import time
import json
import logging
from typing import Dict, Any, Optional
from config import LOG_DIR


class AuditLogger:
    def __init__(self):
        self.log_dir = LOG_DIR
        os.makedirs(self.log_dir, exist_ok=True)
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger("audit_trail")
        self.logger.setLevel(logging.INFO)
        
        log_file = os.path.join(self.log_dir, f"audit_{time.strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def generate_log_id(self) -> str:
        return str(uuid.uuid4())

    def get_timestamp_ms(self) -> int:
        return int(time.time() * 1000)

    def log(self, agent_id: str, ip: str, operation: str, status: str, detail: Dict[str, Any]) -> str:
        log_entry = {
            "log_id": self.generate_log_id(),
            "timestamp": self.get_timestamp_ms(),
            "agent_id": agent_id,
            "ip": ip,
            "operation": operation,
            "status": status,
            "detail": detail
        }
        
        log_json = json.dumps(log_entry, ensure_ascii=False)
        self.logger.info(log_json)
        
        return log_entry["log_id"]

    def log_registration(self, agent_id: str, ip: str, subtype: str, scope: Dict, agent_secret_masked: str, status: str, fail_reason: str = ""):
        detail = {
            "subtype": subtype,
            "scope": scope,
            "agent_secret": agent_secret_masked,
            "fail_reason": fail_reason
        }
        return self.log(agent_id, ip, "register", status, detail)

    def log_authorization(self, agent_id: str, ip: str, token_id: str, applied_scope: Dict, granted_scope: Dict, expire_at: int, status: str, fail_reason: str = ""):
        detail = {
            "token_id": token_id,
            "applied_scope": applied_scope,
            "granted_scope": granted_scope,
            "expire_at": expire_at,
            "fail_reason": fail_reason
        }
        return self.log(agent_id, ip, "authorize", status, detail)

    def log_verification(self, agent_id: str, ip: str, token_id: str, required_scope: Dict, valid: bool, fail_reason: str = ""):
        detail = {
            "token_id": token_id,
            "required_scope": required_scope,
            "valid": valid,
            "fail_reason": fail_reason
        }
        return self.log(agent_id, ip, "verify", "success" if valid else "fail", detail)

    def log_blocked(self, agent_id: str, ip: str, operation: str, reason: str):
        detail = {
            "block_reason": reason
        }
        return self.log(agent_id, ip, operation, "blocked", detail)

    def get_log_file_path(self, date_str: Optional[str] = None) -> str:
        if not date_str:
            date_str = time.strftime('%Y%m%d')
        return os.path.join(self.log_dir, f"audit_{date_str}.log")

    def export_logs(self, start_time: int, end_time: int) -> list:
        result = []
        try:
            log_file = self.get_log_file_path()
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if start_time <= entry.get("timestamp", 0) <= end_time:
                            result.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        return result