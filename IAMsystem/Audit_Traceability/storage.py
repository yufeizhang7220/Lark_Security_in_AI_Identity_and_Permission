import json
import os
from typing import Dict, Any, List
from config import AUDIT_LOGS_PATH, BLACKLIST_PATH


class AuditStorage:
    @staticmethod
    def _ensure_file_exists(file_path: str):
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_audit_logs() -> Dict[str, Any]:
        AuditStorage._ensure_file_exists(AUDIT_LOGS_PATH)
        try:
            with open(AUDIT_LOGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def save_audit_logs(logs: Dict[str, Any]) -> bool:
        try:
            AuditStorage._ensure_file_exists(AUDIT_LOGS_PATH)
            with open(AUDIT_LOGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def load_blacklist() -> Dict[str, Any]:
        AuditStorage._ensure_file_exists(BLACKLIST_PATH)
        try:
            with open(BLACKLIST_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict) or "agents" not in data:
                    return {"agents": [], "ips": [], "users": []}
                return data
        except json.JSONDecodeError:
            return {"agents": [], "ips": [], "users": []}

    @staticmethod
    def save_blacklist(blacklist: Dict[str, Any]) -> bool:
        try:
            AuditStorage._ensure_file_exists(BLACKLIST_PATH)
            with open(BLACKLIST_PATH, 'w', encoding='utf-8') as f:
                json.dump(blacklist, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def add_to_blacklist(agent_id: str = None, ip: str = None, user_id: str = None):
        blacklist = AuditStorage.load_blacklist()
        if agent_id and agent_id not in blacklist["agents"]:
            blacklist["agents"].append(agent_id)
        if ip and ip not in blacklist["ips"]:
            blacklist["ips"].append(ip)
        if user_id and user_id not in blacklist["users"]:
            blacklist["users"].append(user_id)
        AuditStorage.save_blacklist(blacklist)

    @staticmethod
    def is_blacklisted(agent_id: str = None, ip: str = None, user_id: str = None) -> bool:
        blacklist = AuditStorage.load_blacklist()
        if agent_id and agent_id in blacklist["agents"]:
            return True
        if ip and ip in blacklist["ips"]:
            return True
        if user_id and user_id in blacklist["users"]:
            return True
        return False