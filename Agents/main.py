"""
统一Agent服务 - main.py
一个FastAPI实例运行多个Agent
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uvicorn
import logging
import os
import httpx
import json

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
HOST = "0.0.0.0"
PORT = 8787

app = FastAPI(title="统一Agent服务")

LOGS_DIR = os.path.join(AGENTS_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(LOGS_DIR, "unified_agent.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("统一Agent服务")

logger.info("=" * 60)
logger.info("统一Agent服务初始化")
logger.info("=" * 60)


AGENTS = {
    "Agent_indata": {
        "name": "企业数据Agent",
        "description": "负责查询企业内部数据（通讯录、日历、多维表格等）",
        "enabled": True,
        "config": {
            "api_key": "ark-d61ab9da-a6f4-4a5e-94b3-c1ca9c4874eb-0f8ce",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20260423223132-gxqgd"
        }
    },
    "Lark-doc-Agent": {
        "name": "飞书文档助手",
        "description": "负责创建和修改飞书文档，可调用其他Agent获取信息",
        "enabled": True,
        "config": {
            "api_key": "ark-68e0d61c-2646-4a0e-8ac1-7ea35da99d21-a6c8f",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20260423222610-xbx2l"
        }
    },
    "External-Search-Agent": {
        "name": "外部检索Agent",
        "description": "负责从外部公开网站获取信息，无权访问飞书企业内部数据",
        "enabled": True
    }
}

class QueryRequest(BaseModel):
    user_input: Optional[str] = None
    Agent_id: Optional[str] = None
    session_id: Optional[str] = None
    session_datetime: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def setup_logger(name: str):
    """设置日志记录器"""
    log_file = os.path.join(LOGS_DIR, f"{name}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    return logger


@app.get("/")
async def root():
    """根路径 - 显示服务信息"""
    agent_list = []
    for agent_id, info in AGENTS.items():
        agent_list.append({
            "agent_id": agent_id,
            "name": info["name"],
            "description": info["description"],
            "enabled": info["enabled"],
            "api_endpoint": f"/{agent_id}/api/query",
            "health_endpoint": f"/{agent_id}/health"
        })

    return {
        "service": "统一Agent服务",
        "version": "1.0.0",
        "agents": agent_list,
        "endpoints": {
            "root": "/",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """全局健康检查"""
    return {
        "status": "healthy",
        "service": "统一Agent服务",
        "port": PORT,
        "agents": {k: v["enabled"] for k, v in AGENTS.items()}
    }


@app.get("/agents")
async def list_agents():
    """列出所有Agent"""
    return {
        "agents": [
            {
                "agent_id": agent_id,
                "name": info["name"],
                "description": info["description"],
                "enabled": info["enabled"]
            }
            for agent_id, info in AGENTS.items()
        ]
    }


@app.post("/{agent_id}/api/query")
async def agent_query(agent_id: str, request: QueryRequest):
    """通用Agent查询接口"""
    logger.info(f"收到 {agent_id} 请求: {request}")

    if agent_id not in AGENTS:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "error": f"Agent '{agent_id}' 不存在"
            }
        )

    if not AGENTS[agent_id]["enabled"]:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": f"Agent '{agent_id}' 已禁用"
            }
        )

    agent_logger = setup_logger(agent_id)
    agent_logger.info(f"接收请求: {request}")

    try:
        if agent_id == "Agent_indata":
            result = await handle_agent_indata(request, agent_logger)
        elif agent_id == "Lark-doc-Agent":
            result = await handle_lark_doc_agent(request, agent_logger)
        elif agent_id == "External-Search-Agent":
            result = await handle_external_search_agent(request, agent_logger)
        else:
            result = {"success": False, "error": f"Agent '{agent_id}' 处理器未实现"}

        agent_logger.info(f"返回结果: {result}")
        return result

    except Exception as e:
        agent_logger.error(f"处理请求出错: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"系统内部错误: {str(e)}"
            }
        )


async def handle_agent_indata(request: QueryRequest, logger):
    """处理企业数据Agent请求"""
    logger.info("处理 Agent_indata 请求")

    session_id = request.session_id or f"session_{hash(str(request.context))}"
    session_datetime = request.session_datetime or "2024-01-01T00:00:00Z"

    if request.context:
        task_type = request.context.get("task_type", "query")
        query_type = request.context.get("Agent_data", {}).get("query_type", "Contacts")
        output_type = request.context.get("Agent_data", {}).get("output_type", "json")

        logger.info(f"任务类型: {task_type}, 查询类型: {query_type}, 输出类型: {output_type}")

        return {
            "success": True,
            "Agent_id": "Agent_indata",
            "session_id": session_id,
            "session_datetime": session_datetime,
            "context": {
                "task_type": task_type,
                "priority": request.context.get("priority", "user"),
                "Agent_data": {
                    "query_type": query_type,
                    "output_type": output_type,
                    "query_data": {
                        "table": [
                            {"姓名": "张三", "成绩": "90", "班级": "A班"},
                            {"姓名": "李四", "成绩": "85", "班级": "A班"},
                            {"姓名": "王五", "成绩": "88", "班级": "A班"}
                        ]
                    }
                }
            }
        }

    return {
        "success": False,
        "error": "缺少context参数"
    }


async def handle_lark_doc_agent(request: QueryRequest, logger):
    """处理飞书文档助手请求"""
    logger.info("处理 Lark-doc-Agent 请求")

    if not request.user_input:
        return {
            "success": False,
            "error": "缺少user_input参数"
        }

    try:
        import sys
        import subprocess
        import httpx
        lark_doc_agent_dir = os.path.join(AGENTS_DIR, "Lark-doc-Agent")
        if lark_doc_agent_dir not in sys.path:
            sys.path.insert(0, lark_doc_agent_dir)

        from llm import LLMClient

        llm_client = LLMClient()

        TOOLS = [
            {
                "type": "function",
                "function": {
                    "name": "create_feishu_doc",
                    "description": "创建飞书文档，先将文档保存到本地目录，再创建飞书文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "文档标题"},
                            "content": {"type": "string", "description": "文档内容（Markdown格式）"}
                        },
                        "required": ["title", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "call_enterprise_data_agent",
                    "description": "调用企业数据Agent查询企业内部数据（通讯录、日历、多维表格等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_type": {"type": "string", "description": "查询类型：Contacts/Calendar/Base"},
                            "output_type": {"type": "string", "description": "输出类型：json/table/pretty"},
                            "query_data": {"type": "object", "description": "查询条件"}
                        },
                        "required": ["query_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "call_external_search_agent",
                    "description": "调用外部检索Agent搜索公开网站信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索查询内容"},
                            "num_results": {"type": "integer", "description": "返回结果数量，默认5"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        DOCS_DIR = os.path.join(lark_doc_agent_dir, "resource", "docs")
        os.makedirs(DOCS_DIR, exist_ok=True)

        def create_feishu_doc(title: str, content: str) -> dict:
            """创建飞书文档"""
            timestamp = int(hash(title + str(hash(content))) % 1000000)
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
            local_filename = f"{safe_title}_{timestamp}.md"
            local_filepath = os.path.join(DOCS_DIR, local_filename)

            with open(local_filepath, 'w', encoding='utf-8') as f:
                f.write(f"{content}")
            logger.info(f"文档已保存到本地: {local_filepath}")

            relative_filepath = os.path.relpath(local_filepath, lark_doc_agent_dir)

            cmd = [
                "lark-cli", "docs", "+create",
                "--api-version", "v2",
                "--doc-format", "markdown",
                "--title", title,
                "--content", f"@{relative_filepath}"
            ]
            logger.info(f"执行lark-cli命令: {' '.join(cmd)}")

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=lark_doc_agent_dir)
            logger.info(f"lark-cli执行结果：返回码={result.returncode}")

            if result.returncode != 0:
                raise Exception(f"lark-cli执行失败: {result.stderr}")

            data = json.loads(result.stdout)
            if not data.get("ok"):
                raise Exception(f"创建文档失败: {data.get('message')}")

            doc_data = data["data"]["document"]
            return {"doc_id": doc_data["document_id"], "doc_url": doc_data["url"], "local_path": local_filepath}

        async def call_enterprise_data_agent(query_type: str, output_type: str = "json", query_data: dict = None) -> dict:
            """调用企业数据Agent"""
            url = "http://localhost:8787/Agent_indata/api/query"

            payload = {
                "Agent_id": "Lark-doc-Agent",
                "session_id": "session_" + str(hash(query_type)),
                "session_datetime": "2024-01-01T00:00:00Z",
                "context": {
                    "task_type": "query",
                    "priority": "user",
                    "Agent_data": {
                        "query_type": query_type,
                        "output_type": output_type,
                        "query_data": query_data or {}
                    },
                    "timeout": 30
                }
            }

            logger.info(f"调用企业数据Agent: {query_type}")
            logger.info(f"请求数据: {payload}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                logger.info(f"企业数据Agent响应: {response.status_code}")
                return response.json()

        async def call_external_search_agent(query: str, num_results: int = 5) -> dict:
            """调用外部检索Agent - 遵循external_search.py的请求格式规范"""
            url = "http://localhost:8787/External-Search-Agent/api/query"

            payload = {
                "Agent_id": "Lark-doc-Agent",
                "session_id": "session_" + str(hash(query)),
                "session_datetime": "2024-01-01T00:00:00Z",
                "context": {
                    "task_type": "search",
                    "action": "web_search",
                    "priority": "user",
                    "Agent_data": {
                        "query_type": "web",
                        "output_type": "json",
                        "query_data": {
                            "query": query,
                            "num_results": num_results
                        }
                    },
                    "timeout": 30
                }
            }

            logger.info(f"调用外部检索Agent: query={query}, num_results={num_results}")
            logger.info(f"请求数据: {payload}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                logger.info(f"外部检索Agent响应: {response.status_code}")
                return response.json()

        async def execute_tool_call(tool_name: str, tool_args: dict) -> str:
            """执行工具调用"""
            logger.info(f"执行工具调用: {tool_name}")
            logger.info(f"工具参数: {tool_args}")

            if tool_name == "create_feishu_doc":
                result = create_feishu_doc(
                    title=tool_args.get("title", "未命名文档"),
                    content=tool_args.get("content", "")
                )
                logger.info(f"文档创建成功，ID: {result['doc_id']}, URL: {result['doc_url']}")
                return f"文档创建成功！<br>文档ID: {result['doc_id']}<br>文档URL: <a href={result['doc_url']} target=_blank>{result['doc_url']}</a><br>本地路径: {result['local_path']}"

            elif tool_name == "call_enterprise_data_agent":
                result = await call_enterprise_data_agent(
                    query_type=tool_args.get("query_type", "Contacts"),
                    output_type=tool_args.get("output_type", "json"),
                    query_data=tool_args.get("query_data")
                )
                logger.info(f"企业数据Agent调用结果: {result}")
                return json.dumps(result, ensure_ascii=False, indent=2)

            elif tool_name == "call_external_search_agent":
                result = await call_external_search_agent(
                    query=tool_args.get("query", ""),
                    num_results=tool_args.get("num_results", 5)
                )
                logger.info(f"外部检索Agent调用结果: {result}")
                return json.dumps(result, ensure_ascii=False, indent=2)

            else:
                return f"未知工具: {tool_name}"

        messages = [
            {"role": "user", "content": request.user_input}
        ]

        logger.info("调用LLM进行分析")
        response = llm_client.chat_with_tools(messages, TOOLS)
        logger.info(f"LLM响应: {response}")

        while response.get("tool_calls"):
            messages.append(response)

            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                logger.info(f"[Agent] 调用工具: {tool_name}")
                tool_result = await execute_tool_call(tool_name, tool_args)
                logger.info(f"[Agent] 工具结果: {tool_result[:100]}...")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "type": "function",
                    "content": tool_result
                })

            logger.info("再次调用LLM进行分析")
            response = llm_client.chat_with_tools(messages, TOOLS)
            logger.info(f"LLM响应: {response}")

        final_response = response.get("content", "")
        logger.info(f"返回最终响应: {final_response}")

        return {
            "success": True,
            "status": "success",
            "data": {
                "response": final_response
            }
        }

    except Exception as e:
        logger.error(f"处理请求失败: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }


async def handle_external_search_agent(request: QueryRequest, logger):
    """处理外部检索Agent请求"""
    logger.info("处理 External-Search-Agent 请求")

    if not request.context:
        return {
            "success": False,
            "error": "缺少context参数"
        }

    action = request.context.get("action", "")
    query_data = request.context.get("Agent_data", {}).get("query_data", {})

    logger.info(f"操作类型: {action}, 查询数据: {query_data}")

    if action == "web_search":
        query = query_data.get("query", "")
        num_results = query_data.get("num_results", 5)

        results = [
            {
                "title": f"搜索结果 {i+1} for {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"这是关于 '{query}' 的第 {i+1} 条搜索结果摘要"
            }
            for i in range(num_results)
        ]

        return {
            "success": True,
            "results": results,
            "total": len(results),
            "query": query
        }

    elif action == "fetch_content":
        url = query_data.get("url", "")

        return {
            "success": True,
            "data": {
                "url": url,
                "title": f"网页标题 - {url}",
                "content": f"这是从 {url} 获取的网页内容...",
                "fetched_at": "2026-04-26 10:00:00"
            }
        }

    elif action == "analyze_content":
        text = query_data.get("text", "")

        return {
            "success": True,
            "analysis": {
                "word_count": len(text.split()),
                "char_count": len(text),
                "summary": text[:100] + "..." if len(text) > 100 else text,
                "keywords": text.split()[:5]
            }
        }

    return {
        "success": False,
        "error": f"未知操作: {action}"
    }


@app.get("/{agent_id}/health")
async def agent_health(agent_id: str):
    """Agent健康检查"""
    if agent_id not in AGENTS:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "service": agent_id,
                "error": f"Agent '{agent_id}' 不存在"
            }
        )

    if not AGENTS[agent_id]["enabled"]:
        return JSONResponse(
            status_code=403,
            content={
                "status": "disabled",
                "service": agent_id,
                "error": f"Agent '{agent_id}' 已禁用"
            }
        )

    return {
        "status": "healthy",
        "service": agent_id,
        "name": AGENTS[agent_id]["name"],
        "description": AGENTS[agent_id]["description"]
    }


@app.get("/{agent_id}/main")
async def agent_main_page(agent_id: str):
    """返回Agent的前端页面（如果有）"""
    if agent_id == "Lark-doc-Agent":
        web_dir = os.path.join(AGENTS_DIR, "Lark-doc-Agent", "Web")
        html_path = os.path.join(web_dir, "index.html")

        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

    return JSONResponse(
        status_code=404,
        content={
            "error": f"Agent '{agent_id}' 没有前端页面"
        }
    )


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("启动统一Agent服务")
    logger.info(f"API地址: http://{HOST}:{PORT}")
    logger.info("可用Agent:")
    for agent_id, info in AGENTS.items():
        logger.info(f"  - {agent_id}: {info['name']} ({info['description']})")
    logger.info("=" * 60)

    uvicorn.run(app, host=HOST, port=PORT)