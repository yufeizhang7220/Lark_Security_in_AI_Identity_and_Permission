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

# 配置文件路径
STORAGE_DIR = os.path.join(project_root, "Storage")
REG_INFO_FILE = os.path.join(STORAGE_DIR, "IMA_reg_info.json")
ACCESS_TOKENS_FILE = os.path.join(STORAGE_DIR, "AccessTokens.json")

# IAM系统配置
IAM_IDENTITY_ENDPOINT = "http://localhost:9002/IAMsystem/identity"
IAM_AUTH_ENDPOINT = "http://localhost:9001/IAMsystem/auth"

# Agent配置
AGENT_NAME = "Lark-doc-Agent"
AGENT_SCOPE = {
    "doc": ["all"],
    "indata": ["read_contact", "read_calendar", "read_bitable"],
    "online": ["web_search", "fetch_content"],
    "iam": ["apply_token", "verify_token"]
}

# 全局存储：AgentSecret和AccessToken，避免重复申请
AGENT_CONFIG = {
    "agent_id": "",
    "agent_secret": "",
    "access_token": "",
    "token_expire": 0
}

# 工具函数：读取本地注册信息
def load_local_reg_info():
    """加载本地存储的注册信息"""
    try:
        if os.path.exists(REG_INFO_FILE):
            try:
                with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                    reg_info = json.load(f)
                    if AGENT_NAME in reg_info:
                        agent_info = reg_info[AGENT_NAME]
                        AGENT_CONFIG["agent_id"] = agent_info.get("agent_id", "")
                        AGENT_CONFIG["agent_secret"] = agent_info.get("agent_secret", "")
                        return True
            except:
                # 文件为空或损坏，返回False重新注册
                pass
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
            try:
                with open(REG_INFO_FILE, "r", encoding="utf-8") as f:
                    reg_info = json.load(f)
            except:
                # 文件为空或损坏，重置为空字典
                reg_info = {}
        
        reg_info[AGENT_NAME] = agent_info
        with open(REG_INFO_FILE, "w", encoding="utf-8") as f:
            json.dump(reg_info, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

# 工具函数：读取本地AccessToken
def load_local_access_token():
    """加载本地存储的AccessToken，返回有效的token"""
    try:
        current_time = int(time.time())
        if os.path.exists(ACCESS_TOKENS_FILE):
            try:
                with open(ACCESS_TOKENS_FILE, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
                    # 查找Lark-doc-Agent的有效token
                    if AGENT_CONFIG["agent_id"] in tokens:
                        token_info = tokens[AGENT_CONFIG["agent_id"]]
                        # 检查是否有效
                        if token_info.get("expire_at") == -1 or token_info.get("expire_at", 0) > current_time:
                            AGENT_CONFIG["access_token"] = token_info.get("access_token", "")
                            AGENT_CONFIG["token_expire"] = token_info.get("expire_at", 0)
                            return True
            except:
                # 文件为空或损坏，返回False重新申请
                pass
    except:
        pass
    return False

# 工具函数：保存AccessToken到本地
def save_access_token(token_info: Dict):
    """保存AccessToken到本地文件"""
    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)
        tokens = {}
        if os.path.exists(ACCESS_TOKENS_FILE):
            try:
                with open(ACCESS_TOKENS_FILE, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
            except:
                # 文件为空或损坏，重置为空字典
                tokens = {}
        
        tokens[AGENT_CONFIG["agent_id"]] = token_info
        with open(ACCESS_TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=4)
        return True
    except:
        return False

# 服务启动时加载本地配置
load_local_reg_info()
load_local_access_token()

# 身份注册工具
def iam_register_user() -> Dict:
    """注册用户身份到IAM系统"""
    try:
        if AGENT_CONFIG["agent_id"] and AGENT_CONFIG["agent_secret"]:
            return {"success": True, "message": "已完成注册，无需重复注册", "agent_id": AGENT_CONFIG["agent_id"]}
        
        register_data = {
            "Agent_name": AGENT_NAME,
            "subtype": "user",
            "scope": AGENT_SCOPE,
            "ip": "127.0.0.1"
        }
        
        response = httpx.post(
            f"{IAM_IDENTITY_ENDPOINT}/register/user",
            json=register_data,
            timeout=30
        )
        result = response.json()
        
        # 记录IAM注册日志
        from main import write_iam_log
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_iam_log(time_str, "register/user", register_data, result)
        
        if result.get("code") == 201:
            agent_info = result["data"]
            AGENT_CONFIG["agent_id"] = agent_info["agent_id"]
            AGENT_CONFIG["agent_secret"] = agent_info["agent_secret"]
            save_local_reg_info(agent_info)
            return {"success": True, "message": "注册成功", "agent_id": agent_info["agent_id"]}
        else:
            return {"success": False, "error": result.get("message", "注册失败")}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 申请AccessToken工具
def iam_apply_access_token(scope: Dict = None, ttl: int = 3600) -> Dict:
    """申请AccessToken，自动处理注册逻辑"""
    try:
        # 首先检查是否已注册
        if not AGENT_CONFIG["agent_id"] or not AGENT_CONFIG["agent_secret"]:
            reg_result = iam_register_user()
            if not reg_result["success"]:
                return reg_result
        
        # 检查现有token是否有效
        current_time = int(time.time())
        if AGENT_CONFIG["access_token"] and AGENT_CONFIG["token_expire"] > current_time + 60:
            return {"success": True, "access_token": AGENT_CONFIG["access_token"], "expire_at": AGENT_CONFIG["token_expire"]}
        
        # 申请新token
        apply_data = {
            "agent_id": AGENT_CONFIG["agent_id"],
            "agent_secret": AGENT_CONFIG["agent_secret"],
            "applied_scope": scope if scope else AGENT_SCOPE,
            "purpose": "文档生成工具调用",
            "ttl": ttl,
            "token_type": "dynamic"
        }
        
        response = httpx.post(
            f"{IAM_AUTH_ENDPOINT}/apply-token",
            json=apply_data,
            timeout=30
        )
        result = response.json()
        
        # 记录IAM Token申请日志
        from main import write_iam_log
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_iam_log(time_str, "apply-token", apply_data, result)
        
        if result.get("code") == 200:
            token_data = result["data"]
            AGENT_CONFIG["access_token"] = token_data["access_token"]
            AGENT_CONFIG["token_expire"] = token_data["expire_at"]
            save_access_token(token_data)
            return {"success": True, "access_token": token_data["access_token"], "expire_at": token_data["expire_at"]}
        else:
            return {"success": False, "error": result.get("message", "Token申请失败")}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 调用企业数据Agent
def call_indata_agent(query_type: str, query_params: Dict = None) -> Dict:
    """调用企业数据Agent获取内部数据"""
    try:
        # 先获取有效token
        token_result = iam_apply_access_token({"indata": ["read_contact", "read_calendar", "read_bitable"]})
        if not token_result["success"]:
            return token_result
        
        headers = {
            "Authorization": f"Bearer {token_result['access_token']}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "context": {
                "task_type": "query_data",
                "Agent_data": {
                    "query_type": query_type,
                    "query_data": query_params if query_params else {}
                }
            }
        }
        
        response = httpx.post(
            "http://localhost:8787/Agent_indata/api/query",
            json=request_data,
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        # 记录企业数据Agent调用日志
        from main import write_iam_log
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_iam_log(time_str, "call_indata_agent", request_data, result)
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# 调用外部检索Agent
def call_external_search_agent(keyword: str, search_params: Dict = None) -> Dict:
    """调用外部检索Agent获取公开信息"""
    try:
        # 先获取有效token
        token_result = iam_apply_access_token({"online": ["web_search", "fetch_content"]})
        if not token_result["success"]:
            return token_result
        
        headers = {
            "Authorization": f"Bearer {token_result['access_token']}",
            "Content-Type": "application/json"
        }
        
        search_params = search_params if search_params else {}
        # 适配外部检索Agent标准接口格式
        request_data = {
            "action": "web_search",
            "query": keyword,
            "num_results": search_params.get("num_results", 5),
            # 透传其他搜索参数
            **{k: v for k, v in search_params.items() if k != "num_results"}
        }
        
        response = httpx.post(
            "http://localhost:9200/External-Search-Agent/api/query",
            json=request_data,
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        # 兼容原有返回格式，适配旧代码
        if result.get("success") and "results" in result:
            # 将结果格式转换为原有系统期望的格式
            result["data"] = {
                "search_results": result["results"],
                "total": result.get("total", len(result["results"])),
                "query": result.get("query", keyword)
            }
        
        # 记录外部检索Agent调用日志
        from main import write_iam_log
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_iam_log(time_str, "call_external_search_agent", request_data, result)
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# 工具调用逻辑
def call_tool(tool_name: str, params: Dict) -> Dict:
    """调用SKILLS中的工具"""
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
        elif tool_name == "iam_register_user":
            result = iam_register_user()
        elif tool_name == "iam_apply_access_token":
            result = iam_apply_access_token(params.get("scope"), params.get("ttl", 3600))
        elif tool_name == "call_indata_agent":
            result = call_indata_agent(params["query_type"], params.get("query_params"))
        elif tool_name == "call_external_search_agent":
            result = call_external_search_agent(params["keyword"], params.get("search_params"))
        else:
            result = {"error": f"未知工具: {tool_name}"}
        
        return result
    except Exception as e:
        return {"error": str(e)}



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
            "name": "call_indata_agent",
            "description": "调用企业数据Agent获取内部企业数据，包括通讯录、日历、多维表格等信息。当需要查询企业内部数据时使用，比如查询员工信息、会议安排、表格数据等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {"type": "string", "description": "查询类型，可选值：read_contact(查询通讯录)、read_calendar(查询日历)、read_bitable(查询多维表格)"},
                    "query_params": {"type": "object", "description": "查询参数，根据不同查询类型传入对应的参数，比如查询通讯录传入{\"name\": \"张三\"}，查询表格传入{\"table_id\": \"xxx\"}"}
                },
                "required": ["query_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_external_search_agent",
            "description": "调用外部检索Agent获取公开网络信息，支持网页搜索、内容抓取等。当需要查询最新的公开信息、行业动态、新闻资讯、知识百科等外部内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词，描述你要查找的内容"},
                    "search_params": {"type": "object", "description": "搜索参数，可选，比如{\"num\": 10, \"time_range\": \"month\"}指定返回结果数量和时间范围"}
                },
                "required": ["keyword"]
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






if __name__ == "__main__":
    pass
    
    
    



