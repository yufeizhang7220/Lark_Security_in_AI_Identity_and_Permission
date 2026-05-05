import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, 'Storage')
LOGS_DIR = os.path.join(BASE_DIR, 'Logs', 'Identity_Registration_Log')

USERS_FILE = os.path.join(STORAGE_DIR, 'users.json')
BOTS_FILE = os.path.join(STORAGE_DIR, 'bots.json')

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9000
API_PREFIX = '/IAMsystem'

for d in [STORAGE_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)
