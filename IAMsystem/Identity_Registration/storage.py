"""
存储操作模块
负责读取和写入 USERS_table.json 和 BOTS_table.json
"""

import json
import os
from typing import Dict, Any
from config import USERS_TABLE_PATH, BOTS_TABLE_PATH


class Storage:
    """存储管理类"""

    @staticmethod
    def _ensure_file_exists(file_path: str):
        """确保文件存在"""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_users() -> Dict[str, Any]:
        """加载用户表"""
        Storage._ensure_file_exists(USERS_TABLE_PATH)
        try:
            with open(USERS_TABLE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def save_users(users: Dict[str, Any]) -> bool:
        """保存用户表"""
        try:
            Storage._ensure_file_exists(USERS_TABLE_PATH)
            with open(USERS_TABLE_PATH, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def load_bots() -> Dict[str, Any]:
        """加载机器表"""
        Storage._ensure_file_exists(BOTS_TABLE_PATH)
        try:
            with open(BOTS_TABLE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def save_bots(bots: Dict[str, Any]) -> bool:
        """保存机器表"""
        try:
            Storage._ensure_file_exists(BOTS_TABLE_PATH)
            with open(BOTS_TABLE_PATH, 'w', encoding='utf-8') as f:
                json.dump(bots, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False
