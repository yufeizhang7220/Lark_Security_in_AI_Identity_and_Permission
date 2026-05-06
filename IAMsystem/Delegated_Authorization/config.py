"""
委托授权模块配置文件
"""
import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(os.path.dirname(BASE_DIR), "Storage")
LOGS_BASE_DIR = os.path.join(os.path.dirname(BASE_DIR), "Logs", "Delegated_Authorization_Log")

# JWT配置
JWT_SECRET = "your_jwt_secret_key_here_change_in_production"  # 生产环境请修改为复杂密钥
JWT_ALGORITHM = "HS256"
MAX_TOKEN_TTL = 86400  # Token最长有效期24小时

# 存储文件路径
USERS_JSON_PATH = os.path.join(STORAGE_DIR, "users.json")
BOTS_JSON_PATH = os.path.join(STORAGE_DIR, "bots.json")
TOKEN_BLACKLIST_PATH = os.path.join(STORAGE_DIR, "token_blacklist.json")
BLACKLIST_PATH = os.path.join(STORAGE_DIR, "blacklist.json") # 全局黑名单路径
TOKEN_CONFIG_PATH = os.path.join(STORAGE_DIR, "token_config.json") # Token配置路径

# 日志路径配置
APPLY_TOKEN_LOG_DIR = os.path.join(LOGS_BASE_DIR, "Apply_Token")
VERIFY_TOKEN_LOG_DIR = os.path.join(LOGS_BASE_DIR, "Verify_Token")
REVOKE_TOKEN_LOG_DIR = os.path.join(LOGS_BASE_DIR, "Revoke_Token")

# 服务配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9001  # 委托授权模块端口
API_PREFIX = "/IAMsystem/auth"

# 审计接口地址
AUDIT_API_URL = "http://localhost:9000/IAMsystem/audit/logs"

# 自动创建目录
for dir_path in [STORAGE_DIR, APPLY_TOKEN_LOG_DIR, VERIFY_TOKEN_LOG_DIR, REVOKE_TOKEN_LOG_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
