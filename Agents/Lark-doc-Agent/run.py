"""
启动脚本 - run.py
启动飞书文档助手Agent
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from config import AGENT_CONFIG

if __name__ == "__main__":
    print(f"启动 {AGENT_CONFIG['name']}...")
    print(f"端口: {AGENT_CONFIG['port']}")
    print(f"API地址: http://{AGENT_CONFIG['host']}:{AGENT_CONFIG['port']}/{AGENT_CONFIG['name']}/api/query")
    print(f"前端地址: http://{AGENT_CONFIG['host']}:{AGENT_CONFIG['port']}/{AGENT_CONFIG['name']}/main")
    print(f"健康检查: http://{AGENT_CONFIG['host']}:{AGENT_CONFIG['port']}/health")
    print("-" * 60)

    uvicorn.run(
        "agent:app",
        host=AGENT_CONFIG["host"],
        port=AGENT_CONFIG["port"],
        reload=False
    )
