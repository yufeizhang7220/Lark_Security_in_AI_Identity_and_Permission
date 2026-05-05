"""
这里记录Agent的所有可调用的技能
"""
import os
import subprocess
import json
import time
import httpx
from typing import List, Dict, Optional
from config import DOCS_DIR, AGENT_CONFIG as CONFIG

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 工具函数：读取本地注册信息
def load_local_reg_info():
    """加载本地存储的注册信息"""
    try:
        if os.path.exists(REG_INFO_FILE):
            with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                reg_info = json.load(f)
                if AGENT_CONFIG["AgentID"] in reg_info:
                    agent_info = reg_info[AGENT_CONFIG["AgentID"]]
                    AGENT_CONFIG["AgentSecret"] = agent_info.get("AgentSecret", "")
                    return True
    except:
        pass
    return False

# 工具函数：保存注册信息到本地
def save_local_reg_info(agent_info: Dict):
    """保存注册信息到本地文件"""
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        reg_info = {}
        if os.path.exists(REG_INFO_FILE):
            with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                reg_info = json.load(f)
        
        reg_info[agent_info["AgentID"]] = agent_info
        with open(REG_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(reg_info, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

# 工具函数：读取本地AccessToken
def load_local_access_tokens():
    """加载本地存储的AccessToken，返回有效的token"""
    try:
        current_time = int(time.time())
        if os.path.exists(ACCESS_TOKENS_FILE):
            with open(ACCESS_TOKENS_FILE, "r", encoding="utf-8") as f:
                tokens = json.load(f)
                # 查找Lark-doc-Agent的有效token
                for token_id, token_info in tokens.items():
                    if token_info.get("AgentID") == AGENT_CONFIG["AgentID"]:
                        # 检查是否有效
                        if token_info.get("exp") == -1 or token_info.get("exp", 0) > current_time:
                            AGENT_CONFIG["AccessToken"] = token_info.get("AgentSecret", "")
                            AGENT_CONFIG["TokenExpire"] = token_info.get("exp", 0)
                            return True
    except:
        pass
    return False

# 服务启动时加载本地配置
load_local_reg_info()
load_local_access_tokens()

# 工具调用逻辑
def call_tool(tool_name: str, params: Dict) -> Dict:
    """调用SKILLS中的工具或IAM系统API"""
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        result = {}
        if tool_name == "create_feishu_doc":
            result = create_feishu_doc(params["title"], params["content"])
        elif tool_name == "check_doc_create_permission":
            perm = check_doc_create_permission()
            result = {"has_permission": perm["doc_create_permission"]}
        elif tool_name == "login_larkcli":
            login_url = login_larkcli()
            result = {"success": True, "login_url": login_url}
        elif tool_name == "iam_register_agent":
            # 调用IAM身份注册API
            register_data = {
                "AgentID": params.get("AgentID", AGENT_CONFIG["AgentID"]),
                "Subtype": params.get("Subtype", "bot"),
                "scope": params["scope"],
                "ip": params.get("ip", "127.0.0.1")
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Identity_Registration/register/bot",
                json=register_data,
                timeout=30
            )
            result = response.json()
            # 注册成功保存AgentSecret到内存和本地文件
            if result.get("code") == 201:
                agent_info = result["data"]
                AGENT_CONFIG["AgentSecret"] = agent_info["AgentSecret"]
                # 保存到本地文件
                save_local_reg_info({
                    "AgentID": agent_info["AgentID"],
                    "Subtype": agent_info["Subtype"],
                    "scope": agent_info["scope"],
                    "AgentSecret": agent_info["AgentSecret"],
                    "registered_at": agent_info["registered_at"],
                    "ip": register_data["ip"]
                })
        elif tool_name == "iam_apply_access_token":
            # 调用IAM委托授权API
            auth_data = {
                "AgentID": params.get("AgentID", AGENT_CONFIG["AgentID"]),
                "Subtype": params.get("Subtype", "user"),
                "AgentSecret": params["AgentSecret"],
                "purpose": params.get("purpose", "访问系统API"),
                "scope": params["scope"],
                "time": params.get("time", 3600)
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Delegated_Authorization",
                json=auth_data,
                timeout=30
            )
            result = response.json()
            # 申请成功保存AccessToken到内存和本地文件
            if result.get("status") == 601 and result.get("AccessToken"):
                token_info = result["AccessToken"]
                AGENT_CONFIG["AccessToken"] = token_info["AgentSecret"]
                AGENT_CONFIG["TokenExpire"] = token_info["exp"]
                # 保存到本地文件
                save_access_token(token_info)
        elif tool_name == "iam_list_tools":
            # 获取IAM系统所有可用工具列表
            if not AGENT_CONFIG["AccessToken"]:
                return {"error": "缺少有效的AccessToken，请先调用iam_apply_access_token申请令牌"}
            # 构造请求
            request_data = {
                "task_type": "list_tools",
                "AccessToken": {
                    "token_id": "",
                    "AgentID": AGENT_CONFIG["AgentID"],
                    "AgentSecret": AGENT_CONFIG["AccessToken"],
                    "scope": {},
                    "IP": "127.0.0.1",
                    "exp": AGENT_CONFIG["TokenExpire"]
                }
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Request_Invocation",
                json=request_data,
                timeout=30
            )
            result = response.json()
            # 保存会话ID
            if result.get("trace_info", {}).get("session_id"):
                SESSION_CONFIG["session_id"] = result["trace_info"]["session_id"]
        elif tool_name == "iam_list_api":
            # 获取指定Bot的API列表
            if not AGENT_CONFIG["AccessToken"]:
                return {"error": "缺少有效的AccessToken，请先调用iam_apply_access_token申请令牌"}
            request_data = {
                "task_type": "list_api",
                "query_bot": params["query_bot"],
                "AccessToken": {
                    "AgentID": AGENT_CONFIG["AgentID"],
                    "AgentSecret": AGENT_CONFIG["AccessToken"],
                    "IP": "127.0.0.1",
                    "exp": AGENT_CONFIG["TokenExpire"]
                },
                "session_id": SESSION_CONFIG["session_id"]
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Request_Invocation",
                json=request_data,
                timeout=30
            )
            result = response.json()
            # 更新会话ID
            if result.get("trace_info", {}).get("session_id"):
                SESSION_CONFIG["session_id"] = result["trace_info"]["session_id"]
        elif tool_name == "iam_api_detail":
            # 获取API详细信息
            if not AGENT_CONFIG["AccessToken"]:
                return {"error": "缺少有效的AccessToken，请先调用iam_apply_access_token申请令牌"}
            request_data = {
                "task_type": "api_detail",
                "query_bot": params["query_bot"],
                "API_ID": params["API_ID"],
                "AccessToken": {
                    "AgentID": AGENT_CONFIG["AgentID"],
                    "AgentSecret": AGENT_CONFIG["AccessToken"],
                    "IP": "127.0.0.1",
                    "exp": AGENT_CONFIG["TokenExpire"]
                },
                "session_id": SESSION_CONFIG["session_id"],
                "last_require": SESSION_CONFIG["last_require"]
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Request_Invocation",
                json=request_data,
                timeout=30
            )
            result = response.json()
            # 更新会话信息
            if result.get("trace_info", {}):
                SESSION_CONFIG["session_id"] = result["trace_info"].get("session_id", SESSION_CONFIG["session_id"])
                SESSION_CONFIG["last_require"] = result["trace_info"].get("require_id", "")
        elif tool_name == "iam_invoke_api":
            # 调用具体的工具API
            if not AGENT_CONFIG["AccessToken"]:
                return {"error": "缺少有效的AccessToken，请先调用iam_apply_access_token申请令牌"}
            request_data = {
                "task_type": "invoke",
                "query_bot": params["query_bot"],
                "API_ID": params["API_ID"],
                "AccessToken": {
                    "AgentID": AGENT_CONFIG["AgentID"],
                    "AgentSecret": AGENT_CONFIG["AccessToken"],
                    "IP": "127.0.0.1",
                    "exp": AGENT_CONFIG["TokenExpire"]
                },
                "session_id": params.get("session_id", SESSION_CONFIG["session_id"]),
                "last_require": SESSION_CONFIG["last_require"],
                "Agent_data": params["Agent_data"],
                "timeout": params.get("timeout", 30)
            }
            response = httpx.post(
                "http://localhost:9000/IAMsystem/Request_Invocation",
                json=request_data,
                timeout=params.get("timeout", 30)
            )
            result = response.json()
            # 更新会话信息
            if result.get("trace_info", {}):
                SESSION_CONFIG["session_id"] = result["trace_info"].get("session_id", SESSION_CONFIG["session_id"])
                SESSION_CONFIG["last_require"] = result["trace_info"].get("require_id", "")
        else:
            result = {"error": f"未知工具: {tool_name}"}
        
        return result
    except Exception as e:
        return {"error": str(e)}

# 配置文件路径
STORAGE_DIR = os.path.join(project_root, "Storage")
REG_INFO_FILE = os.path.join(STORAGE_DIR, "IMA_reg_info.json")
ACCESS_TOKENS_FILE = os.path.join(STORAGE_DIR, "AccessTokens.json")

# 全局存储：AgentSecret和AccessToken，避免重复申请
AGENT_CONFIG = {
    "AgentID": CONFIG["name"],
    "AgentSecret": "",
    "AccessToken": "",
    "TokenExpire": 0
}

# 全局会话存储
SESSION_CONFIG = {
    "session_id": "",
    "last_require": ""
}

# 工具定义 - 所有可用工具
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_feishu_doc",
            "description": "创建飞书云文档，传入文档标题和内容，返回文档URL和本地保存路径。当用户需要生成正式的飞书文档时使用，是最终输出结果的必须调用工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文档标题"},
                    "content": {"type": "string", "description": "文档内容，支持XML或Markdown格式，优先使用XML格式支持更丰富的样式"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_doc_create_permission",
            "description": "检查当前是否有飞书文档创建权限，返回是否有权限。在首次创建文档前调用，确保有权限操作。",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "login_larkcli",
            "description": "完成lark-cli登录授权，当没有文档创建权限时调用，获取操作权限。",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_apply_access_token",
            "description": "调用IAM系统委托授权API，申请AccessToken，用于访问其他需要权限的API。需要先完成身份注册后才能调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "AgentID": {"type": "string", "description": "已注册的AgentID，默认值为Lark-doc-Agent"},
                    "Subtype": {"type": "string", "description": "身份类型，可选user/visitor/bot，默认值为user"},
                    "AgentSecret": {"type": "string", "description": "注册时获得的AgentSecret，需要用户提前配置"},
                    "purpose": {"type": "string", "description": "申请Token的用途，默认值为访问系统API"},
                    "scope": {"type": "object", "description": "申请的权限范围，格式为{\"数据类型\": [\"操作列表\"]}"},
                    "time": {"type": "integer", "description": "有效期，单位秒，最大86400，默认3600"}
                },
                "required": ["AgentSecret", "scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_register_agent",
            "description": "调用IAM系统身份注册API，注册本Agent到IAM系统，获得AgentSecret，是使用其他IAM API的前提。只需要注册一次即可。",
            "parameters": {
                "type": "object",
                "properties": {
                    "AgentID": {"type": "string", "description": "Agent名称，固定为Lark-doc-Agent"},
                    "Subtype": {"type": "string", "description": "身份类型，固定为bot"},
                    "scope": {"type": "object", "description": "申请的权限范围，比如{\"doc\": [\"all\"], \"online\": [\"all\"]}"},
                    "ip": {"type": "string", "description": "注册IP，默认127.0.0.1"}
                },
                "required": ["scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_list_tools",
            "description": "调用IAM系统Help接口，获取所有已注册的可用工具Bot列表，返回每个Bot的名称和功能描述。当你不知道有哪些工具可以使用时调用。",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_list_api",
            "description": "调用IAM系统Help接口，获取指定工具Bot下的所有API列表，返回API ID、功能描述和所需权限。知道Bot名称后调用此接口查看该工具提供哪些API。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_bot": {"type": "string", "description": "要查询的Bot名称，比如Agent_indata/External-Search-Agent"}
                },
                "required": ["query_bot"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_api_detail",
            "description": "调用IAM系统Help接口，获取指定API的详细信息，包括请求参数格式、响应格式、所需权限。知道Bot和API ID后调用此接口查看如何使用该API。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_bot": {"type": "string", "description": "Bot名称，比如Agent_indata"},
                    "API_ID": {"type": "string", "description": "API ID，从iam_list_api返回结果中获取"}
                },
                "required": ["query_bot", "API_ID"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iam_invoke_api",
            "description": "调用IAM系统统一请求接口，执行具体的工具API调用。获取API详情并确认参数格式后，调用此接口执行实际操作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_bot": {"type": "string", "description": "目标Bot名称"},
                    "API_ID": {"type": "string", "description": "要调用的API ID"},
                    "Agent_data": {"type": "object", "description": "具体的请求参数，根据API详情中的required_json格式传入"},
                    "session_id": {"type": "string", "description": "会话ID，可选，首次调用不需要传，后续调用复用返回的session_id"},
                    "timeout": {"type": "integer", "description": "超时时间，单位秒，默认30"}
                },
                "required": ["query_bot", "API_ID", "Agent_data"]
            }
        }
    }
]

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 5. 查看larkcli的文档创建权限是否授权
def check_doc_create_permission() -> dict:
    """
    功能：检查larkcli是否授权了文档创建权限
    
    :return: {"is_login": True/False, "doc_create_permission": True/False} 
    """
    # 执行指令
    cmd = ["lark-cli", "auth", "check", "--scope", "docx:document:create"]
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60,cwd=project_root)
    data = json.loads(result.stdout)
    return {"is_login": False if "error" in data else True, "doc_create_permission": data["ok"]}

# 6. 登入larkcli
def login_larkcli() -> str:
    """
    功能：登入larkcli
    
    :return: 返回登入链接
    """
    # 执行指令
    cmd = ["lark-cli", "auth", "login","--recommend","--no-wait"]
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60,cwd=project_root)
    data = json.loads(result.stdout)
    log_url=data["verification_url"]
    return log_url

# 7. 使用larkcli创建文档
def create_feishu_doc(title: str, content: str) -> dict:
    """
    功能：创建飞书文档，先保存到本地，再创建飞书文档
    
    :param title: 文档标题
    :param content: 文档内容
    :return: 包含文档ID、URL和本地路径的字典
    """

    # 生成本地文件名
    timestamp = int(hash(title + str(hash(content))) % 1000000)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:20]
    local_filename = f"{safe_title}_{timestamp}.md"
    local_filepath = os.path.join(DOCS_DIR, local_filename)

    # 确保docs目录存在
    os.makedirs(DOCS_DIR, exist_ok=True)

    # 写入本地文件（LLM返回的内容已经包含标题，不需要额外添加）
    with open(local_filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[Agent] 文档已保存到本地: {local_filepath}")

    # 获取相对于项目根目录的相对路径
    relative_filepath = os.path.relpath(local_filepath, project_root)

    # 使用lark-cli创建飞书文档，指定标题避免默认Untitled
    cmd = [
        "lark-cli", "docs", "+create",
        "--api-version", "v2",
        "--doc-format", "markdown",
        "--title", title,
        "--content", f"@{relative_filepath}"
    ]
    print("创建文档命令：", " ".join(cmd))

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, cwd=project_root)

    data = json.loads(result.stdout)

    doc_data = data["data"]["document"]
    return {"doc_id": doc_data["document_id"], "doc_url": doc_data["url"], "local_path": local_filepath}

# 8. 将注册到IMA系统中的身份保存到本地文件
def save_user_info(user_info: dict) -> bool:
    """
    功能：将注册到IMA系统中的user身份保存到本地文件
    以特定格式 添加到 相对于项目根目录的 Storage/IMA_reg_info.json 文件中
    
    :param user_info: 包含user身份信息的字典
    包含字段示例：
        "AgentID":"Lark-doc-Agent",
        "Subtype":"user",
        "scope":{"doc":["all"] , "tablebase":["all"] , "calendar":["all"] , "online":["all"]},
        "AgentSecret":"7s9KpR2tG8xQbA5dF3zC1vN4mH6jY0wU (密钥算法自定义)",
        "registered_at":1745800000,
        "ip": "127.0.0.1"
    """
    # 检查文件是否存在
    if not os.path.exists(f"{project_root}/Storage/IMA_reg_info.json"):
        os.makedirs(f"{project_root}/Storage", exist_ok=True)
    # 写入新user_info
    with open(f"{project_root}/Storage/IMA_reg_info.json", "r+", encoding="utf-8") as f:
        data = json.load(f)
        data[user_info['AgentID']] = user_info
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=4)
    return True

# 9. 将申请的AccessTokenSecret保存到本地文件
def save_access_token(access_token: dict) -> bool:
    """
    功能：将申请的AccessTokenSecret保存到本地文件
    以特定格式 保存到 相对于项目根目录的 Storage/AccessTokens.json 文件中
    
    :param access_token: 包含申请的AccessTokenSecret的字典
    包含字段示例：
        "tk_f3449be846bc42c6b734a3e750cd46a2": {
        "token_id": "tk_f3449be846bc42c6b734a3e750cd46a2",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "online": [
                "all"
            ]
        },
        "AgentSecret": "47058a448425430cb678f47883d315d586cc053e",
        "iat": 1777364339,
        "exp": 1777367339,
        "IP": "127.0.0.1",
        "purpose": "获取企业数据"
        }
    """
    # 检查文件是否存在
    if not os.path.exists(f"{project_root}/Storage/AccessTokens.json"):
        os.makedirs(f"{project_root}/Storage", exist_ok=True)
    # 删除 原文件中 exp 已经过期的内容
    tokens= None
    with open(f"{project_root}/Storage/AccessTokens.json", "r", encoding="utf-8") as f:
        current_time = int(time.time())
        tokens = json.load(f)
        # 遍历字典的key，删除过期的token
        expired_token_ids = []
        for token_id, token_info in tokens.items():
            if token_info['exp'] != -1 and token_info["exp"] < current_time:
                expired_token_ids.append(token_id)
        # 批量删除过期token
        for token_id in expired_token_ids:
            del tokens[token_id]
    # 新token以token_id作为key存入字典
    tokens[access_token["token_id"]] = access_token
    # 写入新token
    with open(f"{project_root}/Storage/AccessTokens.json", "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=4)
    return True


def test_5():
    print(check_doc_create_permission())

def test_6():
    print(login_larkcli())

def test_7():
    doc_list=create_feishu_doc(
"测试文档01", 
"""
## 这是一个测试文档
hello world!
""")
    print(doc_list)

def test_8():
    use_info={
        "AgentID":"test",
        "Subtype":"visitor",
        "scope":{"doc":["all"]},
        "AgentSecret":"7s9KpR2tG8xQbA5dF3zC1vN4mH6jY0wU",
        "registered_at":1745800000,
        "ip": "127.0.0.1"
    }
    print(save_user_info(use_info))

def test_9():
    access_token={
        "token_id": "tk_f3",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "online": [
                "all"
            ]
        },
        "AgentSecret": "47058a448425430cb678f47883d315d586cc053e",
        "iat": 1777364339,
        "exp": 1777367339,
        "IP": "127.0.0.1",
        "purpose": "获取企业数据"
    }
    print(save_access_token(access_token))




if __name__ == "__main__":
    test_9()
    
    
    



