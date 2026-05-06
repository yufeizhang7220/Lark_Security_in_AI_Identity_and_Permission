"""
外部检索Agent API服务
启动端口: 9200
接口路径: /External-Search-Agent/api/query
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.requests import Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
from external_search.main import ExternalSearchAgent
from common.iam_client import IAMClient

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化FastAPI应用
app = FastAPI(
    title="外部检索Agent API",
    description="负责从外部公开网站获取信息，无权访问任何飞书企业内部数据",
    version="1.0.0"
)

# 配置CORS跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化IAM客户端
iam_client = IAMClient()

# 企业数据Agent地址
INDATA_AGENT_URL = "http://localhost:9300/Agent_indata/api/query"  # 企业数据Agent默认地址，根据实际情况修改

# 初始化Agent实例
agent = ExternalSearchAgent()

# 请求参数模型
class QueryRequest(BaseModel):
    action: str = "web_search"  # web_search/fetch_content/analyze_content
    query: Optional[str] = None  # 搜索关键词/要分析的文本
    url: Optional[str] = None  # 要抓取的网页URL
    num_results: int = 5  # 搜索结果数量

# 响应模型
class QueryResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    http_status: int = 200

# 游客相关请求模型
class VisitorApplyTokenRequest(BaseModel):
    agent_id: str
    agent_secret: str

class VisitorCallIndataRequest(BaseModel):
    access_token: str
    query: str

@app.post("/External-Search-Agent/api/query", response_model=QueryResponse, summary="外部检索查询接口")
def query(request: QueryRequest, authorization: Optional[str] = Header(None, alias="Authorization")):
    """
    外部检索统一查询接口（符合IAM系统规范）
    - action: 操作类型 web_search(网络搜索)/fetch_content(网页抓取)/analyze_content(文本分析)
    - query: 搜索关键词或要分析的文本（web_search和analyze_content时必填）
    - url: 要抓取的网页URL（fetch_content时必填）
    - num_results: 搜索结果返回数量，默认5条
    - 请求头必须携带: Authorization: Bearer {access_token} （从IAM系统申请的有效AccessToken）
    """
    try:
        # 严格按照IAM规范提取AccessToken（兼容大小写）
        access_token = None
        if authorization:
            auth_str = authorization.strip()
            if auth_str.lower().startswith("bearer "):
                access_token = auth_str[7:].strip()  # 去掉"Bearer "前缀
        
        # 调试日志：打印提取到的Token
        print(f"[API层] 提取到的AccessToken前缀: {access_token[:20] if access_token else '空'}")
        
        # 没有AccessToken直接返回401
        if not access_token or len(access_token) < 10:  # 合法JWT Token长度至少大于10
            return {
                "success": False,
                "error_code": "AUTH_001",
                "error_message": "缺少合法的AccessToken，请在请求头携带Authorization: Bearer {access_token}",
                "http_status": 401
            }
        
        # 构造任务请求
        task = {
            "context": {
                "action": request.action,
                "Agent_data": {
                    "query_data": {
                        "query": request.query,
                        "url": request.url,
                        "num_results": request.num_results
                    }
                }
            },
            "access_token": access_token
        }
        
        # 执行任务
        result = agent.execute_task(task)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"服务内部错误: {str(e)}"
        )

@app.get("/health", summary="健康检查接口")
def health_check():
    return {
        "status": "healthy",
        "agent_id": agent.agent_id,
        "supported_actions": agent.allowed_actions
    }

@app.get("/", summary="前端页面")
async def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

@app.post("/api/visitor/register", response_model=QueryResponse, summary="注册游客身份")
async def visitor_register():
    """注册游客身份，自动生成唯一的Agent名称，分配基础权限"""
    try:
        import random
        import string
        # 生成随机的Agent名称
        agent_name = f"visitor_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
        
        # 调用IAM身份注册接口
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9002/IAMsystem/identity/register/user",
                json={
                    "Agent_name": agent_name,
                    "subtype": "visitor",
                    "scope": {
                        "online": ["web_search", "fetch_content", "analyze_content"],
                        "indata": ["read_contact", "read_calendar", "read_bitable"],
                        "iam": ["apply_token", "verify_token"]
                    }
                }
            )
            result = response.json()
            
            if result.get("code") == 201:
                return {
                    "success": True,
                    "data": result["data"],
                    "http_status": 200
                }
            else:
                return {
                    "success": False,
                    "error_code": str(result.get("code", "REG_FAIL")),
                    "error_message": result.get("message", "注册失败"),
                    "http_status": 400
                }
    except Exception as e:
        return {
            "success": False,
            "error_code": "SERVER_ERROR",
            "error_message": f"注册失败: {str(e)}",
            "http_status": 500
        }

@app.post("/api/visitor/apply-token", response_model=QueryResponse, summary="申请AccessToken")
async def visitor_apply_token(request: VisitorApplyTokenRequest):
    """使用AgentID和AgentSecret申请AccessToken"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:9001/IAMsystem/auth/apply-token",
                json={
                    "agent_id": request.agent_id,
                    "agent_secret": request.agent_secret,
                    "applied_scope": {
                        "online": ["web_search", "fetch_content", "analyze_content"],
                        "indata": ["read_contact", "read_calendar", "read_bitable"]
                    },
                    "purpose": "游客访问企业数据",
                    "ttl": 3600
                }
            )
            result = response.json()
            
            if result.get("code") == 200:
                return {
                    "success": True,
                    "data": result["data"],
                    "http_status": 200
                }
            else:
                return {
                    "success": False,
                    "error_code": str(result.get("code", "TOKEN_FAIL")),
                    "error_message": result.get("message", "Token申请失败"),
                    "http_status": 400
                }
    except Exception as e:
        return {
            "success": False,
            "error_code": "SERVER_ERROR",
            "error_message": f"Token申请失败: {str(e)}",
            "http_status": 500
        }

@app.post("/api/visitor/call-indata", response_model=QueryResponse, summary="调用企业数据Agent")
async def visitor_call_indata(request: VisitorCallIndataRequest):
    """使用AccessToken调用企业数据Agent"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                INDATA_AGENT_URL,
                headers={
                    "Authorization": f"Bearer {request.access_token}"
                },
                json={
                    "context": {
                        "task_type": "query",
                        "priority": "normal",
                        "Agent_data": {
                            "query_type": "common",
                            "output_type": "json",
                            "query_data": {
                                "query": request.query
                            }
                        }
                    }
                }
            )
            result = response.json()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": result,
                    "http_status": 200
                }
            else:
                return {
                    "success": False,
                    "error_code": str(response.status_code),
                    "error_message": result.get("message", "调用企业数据Agent失败"),
                    "http_status": response.status_code
                }
    except Exception as e:
        return {
            "success": False,
            "error_code": "SERVER_ERROR",
            "error_message": f"调用失败: {str(e)}",
            "http_status": 500
        }

if __name__ == "__main__":
    import uvicorn
    print("外部检索Agent API服务启动中...")
    print(f"前端页面地址: http://localhost:9200/")
    print(f"接口地址: http://localhost:9200/External-Search-Agent/api/query")
    print(f"接口文档: http://localhost:9200/docs")
    uvicorn.run(app, host="0.0.0.0", port=9200)
