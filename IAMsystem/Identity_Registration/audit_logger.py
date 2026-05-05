import json
import os
import time
import uuid
import requests
from datetime import datetime
from config import LOGS_DIR, AUDIT_API_URL
from typing import Dict, Any

# 审计模块上报接口地址
AUDIT_RECORD_URL = "http://localhost:9000/IAMsystem/audit/record"
AUDIT_REGISTRATION_URL = "http://localhost:9000/IAMsystem/audit/record/registration"
AUDIT_VERIFICATION_URL = "http://localhost:9000/IAMsystem/audit/record/verification"

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
        # 上报到审计模块
        audit_data = {
            "agent_id": agent_id,
            "ip": ip,
            "subtype": detail.get("subtype", ""),
            "scope": detail.get("scope", {}),
            "agent_secret": detail.get("agent_secret", "****"),
            "status": status,
            "fail_reason": detail.get("fail_reason", "")
        }
        AuditLogger.report_audit_log(AUDIT_REGISTRATION_URL, audit_data)
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
        # 上报到审计模块
        audit_data = {
            "agent_id": agent_id,
            "ip": ip,
            "token_id": "",
            "required_scope": detail.get("scope", {}),
            "valid": detail.get("valid", False),
            "fail_reason": detail.get("fail_reason", "")
        }
        AuditLogger.report_audit_log(AUDIT_VERIFICATION_URL, audit_data)
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
    @staticmethod
    def call_audit_api(agent_id: str, operation: str, detail: Dict[str, Any]) -> bool:
        """调用审计接口检查操作是否合法"""
        try:
            now = int(time.time())
            request_data = {
                "agent_id": agent_id,
                "start_time": now - 3600,
                "end_time": now,
                "operation": operation,
                "detail": detail
            }
            response = requests.post(AUDIT_API_URL, json=request_data, timeout=3)
            if response.status_code == 200:
                result = response.json()
                return result.get("valid", False)
            return True  # 审计接口不可用时默认放行
        except Exception:
            return True

    @staticmethod
    def report_audit_log(url: str, data: Dict[str, Any]) -> bool:
        """上报日志到审计模块"""
        try:
            requests.post(url, json=data, timeout=2)
            return True
        except Exception:
            return False  # 上报失败不影响业务
