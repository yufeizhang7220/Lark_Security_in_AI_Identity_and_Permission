import json
import os
import time
import uuid
from datetime import datetime
from config import LOGS_DIR
from typing import Dict, Any

class AuditLogger:
    @staticmethod
    def _get_log_file_path() -> str:
        today = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(LOGS_DIR, f'registration_{today}.log')
        return log_file

    @staticmethod
    def _ensure_log_file() -> str:
        log_file = AuditLogger._get_log_file_path()
        if not os.path.exists(log_file):
            with open(log_file, 'w', encoding='utf-8') as f:
                pass
        return log_file

    @staticmethod
    def _generate_log_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _append_log(log_entry: Dict[str, Any]) -> bool:
        try:
            log_file = AuditLogger._ensure_log_file()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            return True
        except Exception:
            return False

    @staticmethod
    def log_register(
        agent_id: str,
        ip: str,
        status: str,
        detail: Dict[str, Any],
        agent_name: str = ""
    ) -> bool:
        log_entry = {
            "log_id": AuditLogger._generate_log_id(),
            "timestamp": int(time.time() * 1000),
            "agent_id": agent_id,
            "agent_name": agent_name,
            "ip": ip,
            "operation": "register",
            "status": status,
            "detail": detail
        }
        return AuditLogger._append_log(log_entry)

    @staticmethod
    def log_verify(
        agent_id: str,
        ip: str,
        status: str,
        detail: Dict[str, Any]
    ) -> bool:
        log_entry = {
            "log_id": AuditLogger._generate_log_id(),
            "timestamp": int(time.time() * 1000),
            "agent_id": agent_id,
            "ip": ip,
            "operation": "verify",
            "status": status,
            "detail": detail
        }
        return AuditLogger._append_log(log_entry)

    @staticmethod
    def get_recent_logs(limit: int = 100) -> list:
        log_file = AuditLogger._get_log_file_path()
        if not os.path.exists(log_file):
            return []
        logs = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        logs.append(json.loads(line))
            return logs[-limit:]
        except Exception:
            return []
