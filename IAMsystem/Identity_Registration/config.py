import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IAMSYSTEM_DIR = os.path.dirname(BASE_DIR) # IAMsystem根目录

# 统一使用根目录下的存储和日志路径
STORAGE_DIR = os.path.join(IAMSYSTEM_DIR, 'Storage')
LOGS_DIR = os.path.join(IAMSYSTEM_DIR, 'Logs', 'Identity_Registration_Log')

USERS_FILE = os.path.join(STORAGE_DIR, 'users.json')
BOTS_FILE = os.path.join(STORAGE_DIR, 'bots.json')
BLACKLIST_PATH = os.path.join(STORAGE_DIR, 'blacklist.json') # 全局黑名单路径

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9002 # 调整端口避免和审计模块冲突（审计模块用9000）
API_PREFIX = '/IAMsystem/identity'
# 审计接口地址
AUDIT_API_URL = "http://localhost:9000/IAMsystem/audit/logs"
for d in [STORAGE_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)
