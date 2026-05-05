import uvicorn
from fastapi import FastAPI
from app import router as audit_router
from config import SERVER_HOST, SERVER_PORT, API_PREFIX

app = FastAPI(title="IAM审计追溯模块", version="1.0")

app.include_router(audit_router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"message": "IAM审计追溯模块 API"}


if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)