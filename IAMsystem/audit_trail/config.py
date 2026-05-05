import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IAMSYSTEM_DIR = os.path.dirname(BASE_DIR)

LOG_DIR = os.path.join(IAMSYSTEM_DIR, "Logs", "audit_trail_Log")
STORAGE_DIR = os.path.join(IAMSYSTEM_DIR, "Storage")

AUDIT_LOGS_PATH = os.path.join(STORAGE_DIR, "audit_logs.json")
BLACKLIST_PATH = os.path.join(STORAGE_DIR, "blacklist.json")

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9000

API_PREFIX = "/IAMsystem/audit"

MAX_REQUESTS_PER_HOUR = 100
MAX_FAILED_ATTEMPTS = 5
ANOMALY_CHECK_INTERVAL = 3600

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)