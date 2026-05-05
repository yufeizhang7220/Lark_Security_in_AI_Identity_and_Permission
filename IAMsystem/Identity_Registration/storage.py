import json
import os
import bcrypt
from typing import Dict, List, Any, Optional
from config import USERS_FILE, BOTS_FILE, BLACKLIST_PATH

DEFAULT_USERS = {
    "_说明": "用户/访客身份存储表，存储所有普通用户和访客身份信息",
    "fields_说明": {
        "agent_id": "系统生成的唯一用户ID，全局唯一",
        "agent_name": "用户自定义名称",
        "subtype": "身份类型：user（普通用户）/visitor（访客）",
        "agent_secret": "bcrypt加密后的用户密钥，不可逆",
        "scope": "用户的静态权限集合，JSON对象",
        "ip": "注册时绑定的IP地址",
        "registered_at": "注册时间戳（秒）",
        "status": "状态：active（正常）/disabled（禁用）"
    },
    "data": []
}

DEFAULT_BOTS = {
    "_说明": "机器Agent身份存储表，存储所有注册的Bot身份信息",
    "fields_说明": {
        "bot_id": "系统生成的唯一BotID，全局唯一",
        "bot_name": "Bot的名称",
        "agent_secret": "bcrypt加密后的Bot密钥，不可逆",
        "scope": "Bot自身的静态权限集合，JSON对象",
        "sub_scope": "不同身份调用该Bot时的权限映射表，key是身份类型，value是对应的权限范围",
        "ip": "注册时绑定的IP地址",
        "api_endpoint": "Bot提供服务的API地址",
        "registered_at": "注册时间戳（秒）",
        "status": "状态：active（正常）/disabled（禁用）/pending（待审核）"
    },
    "data": []
}

class Storage:
    @staticmethod
    def _ensure_file_exists(file_path: str, default_data: Dict) -> None:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_users() -> Dict:
        Storage._ensure_file_exists(USERS_FILE, DEFAULT_USERS)
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_USERS.copy()

    @staticmethod
    def save_users(users: Dict) -> bool:
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def load_bots() -> Dict:
        Storage._ensure_file_exists(BOTS_FILE, DEFAULT_BOTS)
        try:
            with open(BOTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_BOTS.copy()

    @staticmethod
    def save_bots(bots: Dict) -> bool:
        try:
            with open(BOTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(bots, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def find_user_by_name(agent_name: str) -> Optional[Dict]:
        users = Storage.load_users()
        for user in users.get("data", []):
            if user.get("agent_name") == agent_name:
                return user
        return None

    @staticmethod
    def find_user_by_id(agent_id: str) -> Optional[Dict]:
        users = Storage.load_users()
        for user in users.get("data", []):
            if user.get("agent_id") == agent_id:
                return user
        return None

    @staticmethod
    def find_bot_by_name(bot_name: str) -> Optional[Dict]:
        bots = Storage.load_bots()
        for bot in bots.get("data", []):
            if bot.get("bot_name") == bot_name:
                return bot
        return None

    @staticmethod
    def find_bot_by_id(bot_id: str) -> Optional[Dict]:
        bots = Storage.load_bots()
        for bot in bots.get("data", []):
            if bot.get("bot_id") == bot_id:
                return bot
        return None

    @staticmethod
    def add_user(user_data: Dict) -> bool:
        users = Storage.load_users()
        users["data"].append(user_data)
        return Storage.save_users(users)

    @staticmethod
    def add_bot(bot_data: Dict) -> bool:
        bots = Storage.load_bots()
        bots["data"].append(bot_data)
        return Storage.save_bots(bots)

    @staticmethod
    def hash_secret(secret: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(secret.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
        try:
            return bcrypt.checkpw(plain_secret.encode('utf-8'), hashed_secret.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def read_global_blacklist() -> Dict:
        """读取全局黑名单文件"""
        if not os.path.exists(BLACKLIST_PATH):
            return {"agents": [], "ips": [], "users": []}
        try:
            with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"agents": [], "ips": [], "users": []}
    
    @staticmethod
    def is_in_blacklist(agent_id: str = "", ip: str = "") -> bool:
        """检查AgentID/用户ID/IP是否在全局黑名单中"""
        blacklist = Storage.read_global_blacklist()
        # 检查Agent/用户黑名单
        if agent_id:
            if agent_id in blacklist.get("agents", []) or agent_id in blacklist.get("users", []):
                return True
        # 检查IP黑名单
        if ip:
            if ip in blacklist.get("ips", []):
                return True
        return False
