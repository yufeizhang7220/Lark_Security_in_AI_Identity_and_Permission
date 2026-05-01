"""
身份注册模块主入口
启动命令: python main.py
"""

import uvicorn
from fastapi import FastAPI
from app import router
from config import API_PREFIX, SERVER_HOST, SERVER_PORT

app = FastAPI(title="IAM System - Identity Registration")

app.include_router(router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {
        "service": "IAM System - Identity Registration",
        "version": "2.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "IAMsystem"
    }


if __name__ == "__main__":
    print(f"启动身份注册服务: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"API文档: http://localhost:{SERVER_PORT}/docs")
    print(f"健康检查: http://localhost:{SERVER_PORT}/health")
    print(f"注册接口: POST http://localhost:{SERVER_PORT}{API_PREFIX}/register")
    print(f"机器注册: POST http://localhost:{SERVER_PORT}{API_PREFIX}/register/bot")
    print(f"查询API: GET http://localhost:{SERVER_PORT}{API_PREFIX}/bot/{{AgentID}}/api/{{api_id}}")

    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True
    )
