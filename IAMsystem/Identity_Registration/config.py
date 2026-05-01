"""
身份注册模块配置
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STORAGE_DIR = os.path.join(BASE_DIR, "Storage")

USERS_TABLE_PATH = os.path.join(STORAGE_DIR, "USERS_table.json")
BOTS_TABLE_PATH = os.path.join(STORAGE_DIR, "BOTS_table.json")

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9000

API_PREFIX = "/IAMsystem/Identity_Registration"
