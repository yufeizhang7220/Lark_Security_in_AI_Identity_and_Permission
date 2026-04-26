"""
飞书文档助手Agent - agent.py
真正的自主决策Agent，使用Function Calling让大模型自主调用工具
"""

import json
import subprocess
from typing import Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import httpx
import os
import logging
import time

from config import AGENT_CONFIG, LLM_CONFIG, OTHER_AGENTS
from llm import LLMClient


app = FastAPI(title=AGENT_CONFIG["name"])

# 初始化LLM客户端
llm_client = LLMClient()

# 获取Web目录的路径
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Web")

# 获取resource目录的路径
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource")
DOCS_DIR = os.path.join(RESOURCE_DIR, "docs")
LOGS_DIR = os.path.join(RESOURCE_DIR, "logs")

# 确保logs目录存在
os.makedirs(LOGS_DIR, exist_ok=True)

# 配置日志
log_file = os.path.join(LOGS_DIR, "lark_doc_agent.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("飞书文档助手")

logger.info("飞书文档助手Agent初始化成功")
logger.info(f"配置: {AGENT_CONFIG}")
logger.info(f"LLM配置: {LLM_CONFIG}")

# 工具定义
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
                    "limit_num": {"type": "integer", "description": "查询数量"},
                    "source": {"type": "string", "description": "查询来源"},
                    "query_data": {"type": "string", "description": "查询内容"}
                },
                "required": ["query_data"]
            }
        }
    }
]


class QueryRequest(BaseModel):
    user_input: str


class QueryResponse(BaseModel):
    status: str
    data: Any = None
    error: str | None = None


def create_feishu_doc(title: str, content: str) -> dict:
    """创建飞书文档，先保存到本地，再创建飞书文档"""

    # 生成本地文件名
    timestamp = int(hash(title + str(hash(content))) % 1000000)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
    local_filename = f"{safe_title}_{timestamp}.md"
    local_filepath = os.path.join(DOCS_DIR, local_filename)

    # 确保docs目录存在
    os.makedirs(DOCS_DIR, exist_ok=True)

    # 写入本地文件
    with open(local_filepath, 'w', encoding='utf-8') as f:
        f.write(f"{content}")
    print(f"[Agent] 文档已保存到本地: {local_filepath}")

    # 获取相对于项目根目录的相对路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    relative_filepath = os.path.relpath(local_filepath, project_root)

    # 使用lark-cli创建飞书文档，需要使用相对路径
    cmd = [
        "lark-cli", "docs", "+create",
        "--api-version", "v2",
        "--doc-format", "markdown",
        "--title", title,
        "--content", f"@{relative_filepath}"
    ]
    logger.info(f"执行lark-cli命令: {' '.join(cmd)}")
    logger.info(f"命令执行目录: {project_root}")
    logger.info(f"使用文件: {relative_filepath}")
    print("创建文档命令：", " ".join(cmd))

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=project_root)
    logger.info(f"lark-cli执行结果：返回码={result.returncode}")
    if result.stdout:
        logger.info(f"lark-cli输出：{result.stdout}")
    if result.stderr:
        logger.error(f"lark-cli错误：{result.stderr}")
    if result.returncode != 0:
        logger.error(f"lark-cli执行失败: {result.stderr}")
        raise Exception(f"lark-cli执行失败: {result.stderr}")

    data = json.loads(result.stdout)
    if not data.get("ok"):
        logger.error(f"创建文档失败: {data.get('message')}")
        raise Exception(f"创建文档失败: {data.get('message')}")

    doc_data = data["data"]["document"]
    return {"doc_id": doc_data["document_id"], "doc_url": doc_data["url"], "local_path": local_filepath}


async def call_enterprise_data_agent(query_type: str, output_type: str = "json", query_data: dict = None) -> dict:
    """调用企业数据Agent"""
    agent_config = OTHER_AGENTS["enterprise_data_agent"]
    url = f"{agent_config['url']}/api/query"

    payload = {
        "Agent_id": AGENT_CONFIG["name"],
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

    try:
        logger.info(f"调用企业数据Agent: {query_type}")
        logger.info(f"请求数据: {payload}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            logger.info(f"企业数据Agent响应: {response.status_code}, {response.text}")
            return response.json()
    except Exception as e:
        logger.error(f"调用企业数据Agent失败: {str(e)}")
        return {"error": f"调用企业数据Agent失败: {str(e)}"}


async def call_external_search_agent(limit_num: int = 5, source: str = "web", query_data: str = "") -> dict:
    """调用外部检索Agent"""
    agent_config = OTHER_AGENTS["external_search_agent"]
    url = f"{agent_config['url']}/api/query"

    payload = {
        "Agent_id": AGENT_CONFIG["name"],
        "session_id": "session_" + str(hash(query_data)),
        "session_datetime": "2024-01-01T00:00:00Z",
        "context": {
            "task_type": "search",
            "action": "search_web",
            "priority": "user",
            "Agent_data": {
                "limit_num": limit_num,
                "source": source,
                "query_data": query_data
            },
            "timeout": 30
        }
    }

    try:
        logger.info(f"调用外部检索Agent: {query_data}")
        logger.info(f"请求数据: {payload}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            logger.info(f"外部检索Agent响应: {response.status_code}, {response.text}")
            return response.json()
    except Exception as e:
        logger.error(f"调用外部检索Agent失败: {str(e)}")
        return {"error": f"调用外部检索Agent失败: {str(e)}"}


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
            limit_num=tool_args.get("limit_num", 5),
            source=tool_args.get("source", "web"),
            query_data=tool_args.get("query_data", "")
        )
        logger.info(f"外部检索Agent调用结果: {result}")
        return json.dumps(result, ensure_ascii=False, indent=2)

    else:
        logger.warning(f"未知工具: {tool_name}")
        return f"未知工具: {tool_name}"


@app.get("/health")
async def health():
    return {"status": "healthy", "service": AGENT_CONFIG["name"]}


@app.get(f"/{AGENT_CONFIG['name']}/main")
async def main_page():
    """返回前端页面"""
    html_path = os.path.join(WEB_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post(f"/{AGENT_CONFIG['name']}/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        logger.info(f"接收查询请求: {request.user_input}")
        messages = [
            {"role": "user", "content": request.user_input}
        ]

        # 第一次调用LLM
        logger.info("调用LLM进行分析")
        response = llm_client.chat_with_tools(messages, TOOLS)
        logger.info(f"LLM响应: {response}")

        # 处理函数调用
        while response.get("tool_calls"):
            # 添加助手消息
            messages.append(response)

            # 执行工具调用
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                logger.info(f"[Agent] 调用工具: {tool_name}")
                tool_result = await execute_tool_call(tool_name, tool_args)
                logger.info(f"[Agent] 工具结果: {tool_result[:100]}...")

                # 添加工具结果消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "type": "function",
                    "content": tool_result
                })

            # 再次调用LLM
            logger.info("再次调用LLM进行分析")
            response = llm_client.chat_with_tools(messages, TOOLS)
            logger.info(f"LLM响应: {response}")

        # 返回最终回复
        final_response = response["content"]
        logger.info(f"返回最终响应: {final_response}")
        return QueryResponse(status="success", data={"response": final_response})

    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return QueryResponse(status="error", error=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host=AGENT_CONFIG["host"], port=AGENT_CONFIG["port"])
