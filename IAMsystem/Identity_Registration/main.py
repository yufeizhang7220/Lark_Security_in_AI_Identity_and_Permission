from fastapi import FastAPI
import uvicorn
from config import API_PREFIX, SERVER_HOST, SERVER_PORT
from app import router

app = FastAPI(title="IAM System - Identity Registration", version="2.0")

app.include_router(router, prefix=API_PREFIX)

@app.get("/")
async def root():
    return {
        "service": "IAM System - Identity Registration",
        "version": "2.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True
    )
