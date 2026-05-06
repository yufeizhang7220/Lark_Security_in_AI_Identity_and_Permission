from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from volcenginesdkarkruntime import Ark
import json
import time
import os
import sys
import httpx
from typing import List, Dict, Optional

# 导入配置和SKILLS
from config import AGENT_CONFIG, LLM_CONFIG, DOCS_DIR, LOG_DIR, WEBPAGES_DIR
import SKILLS
from SKILLS import TOOLS, call_tool, AGENT_CONFIG as SKILLS_AGENT_CONFIG

app = FastAPI(title="Lark-doc-Agent", version="1.0")

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 转换为绝对路径
LOG_DIR_ABS = os.path.join(PROJECT_ROOT, LOG_DIR)
WEBPAGES_DIR_ABS = os.path.join(PROJECT_ROOT, WEBPAGES_DIR)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=WEBPAGES_DIR_ABS), name="static")

# 初始化火山引擎客户端
client = Ark(
    api_key=LLM_CONFIG["api_key"],
    base_url=LLM_CONFIG["base_url"]
)

# 确保日志目录存在
def ensure_log_dirs():
    """确保所有日志目录存在"""
    try:
        os.makedirs(LOG_DIR_ABS, exist_ok=True)
    except:
        pass

# 启动时创建日志目录
ensure_log_dirs()

# 请求模型
class DocGenerateRequest(BaseModel):
    title: str
    user_input: str

# 日志工具函数
def write_user_log(
    time_str: str,
    title: str,
    user_input: str,
    required_tools: List[str],
    used_tools: List[str],
    result: str,
    local_path: str,
    doc_url: str
):
    """写入用户输入日志，出错不影响主流程"""
    try:
        ensure_log_dirs()
        log_path = os.path.join(LOG_DIR_ABS, "user_about.log")
        log_line = f"[{time_str}] [{title}] [{user_input}] [{','.join(required_tools)}] [{','.join(used_tools)}] [{result}] [{local_path}] [{doc_url}]\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass

def write_skill_log(time_str: str, skill_list: List[str]):
    """写入skill使用日志，出错不影响主流程"""
    try:
        ensure_log_dirs()
        log_path = os.path.join(LOG_DIR_ABS, "skills_about.log")
        log_line = f"[{time_str}] [{','.join(skill_list)}]\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass

def write_iam_log(time_str: str, api: str, request_json: Dict, response_json: Dict):
    """写入IAM系统调度日志，出错不影响主流程"""
    try:
        ensure_log_dirs()
        log_path = os.path.join(LOG_DIR_ABS, "IAM_about.log")
        log_line = f"[{time_str}] [{api}] [{json.dumps(request_json, ensure_ascii=False)}] [{json.dumps(response_json, ensure_ascii=False)}]\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass



# LLM调用函数，支持工具调用
def call_llm_with_tools(messages: List[Dict]) -> Dict:
    """调用LLM，支持工具调用，返回完整响应（转为普通字典避免序列化问题）"""
    response = client.chat.completions.create(
        model=LLM_CONFIG["model"],
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    message = response.choices[0].message
    # 转为普通字典，避免对象序列化问题
    message_dict = {
        "role": message.role,
        "content": message.content
    }
    if message.tool_calls:
        # 工具调用也转为字典格式
        message_dict["tool_calls"] = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
            } for tc in message.tool_calls
        ]
    return message_dict

# 前端页面路由
@app.get("/Lark-doc-Agent/Web")
async def web_page():
    """返回前端页面"""
    return FileResponse(os.path.join(WEBPAGES_DIR_ABS, "index.html"))

# 核心API路由
@app.post("/Lark-doc-Agent")
async def generate_doc(request: DocGenerateRequest):
    """生成飞书文档核心接口 - 支持自主工具调用的真正Agent"""
    start_time = time.time()
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logs = []
    used_tools = []
    
    try:
        logs.append(f"🚀 启动飞书文档助手Agent")
        logs.append(f"📝 文档标题: {request.title}")
        logs.append(f"💡 用户需求: {request.user_input}")


        # 1. 系统提示词，告诉LLM身份和能力
        system_prompt = f"""你是飞书文档助手Agent，专业的文档生成专家。
你的核心能力：
1. 自主判断用户需求，生成高质量的专业文档
2. 可以自主选择调用工具完成任务，不需要询问用户
3. 支持访问企业内部数据和外部公开信息，自动整合多来源内容
4. 最后直接返回完整的文档内容即可，不需要调用create_feishu_doc工具，系统会自动为你创建飞书文档

工具使用规则：
- 根据用户需求判断是否需要调用相关工具，有合适的工具优先使用工具获取信息
- 需要查询企业内部数据（通讯录、日历、多维表格等）时，优先调用call_indata_agent工具
- 需要查询公开网络信息（新闻、资讯、知识、行业动态等）时，优先调用call_external_search_agent工具
- 所有工具调用结果都要整合到最终的文档内容中
- 必须确保内容丰富、结构清晰，符合企业文档规范
- 最后直接返回完整的文档内容即可，不需要调用create_feishu_doc工具，系统会自动为你创建飞书文档。"""

        # 用户输入
        user_prompt = f"""文档标题：{request.title}
用户需求：{request.user_input}
请自主选择合适的工具完成需求，最终生成完整的飞书文档。"""

        # 初始化消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 2. Agent循环：调用LLM->执行工具调用，直到完成任务
        max_rounds = 10  # 最大调用轮次限制
        current_round = 0
        doc_content = ""
        create_result = None

        while current_round < max_rounds:
            current_round += 1
            logs.append(f"\n🔄 第 {current_round} 轮处理")

            # 调用LLM
            llm_response = call_llm_with_tools(messages)
            messages.append(llm_response)

            # 检查是否需要调用工具
            if "tool_calls" in llm_response and llm_response["tool_calls"]:
                for tool_call in llm_response["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_params = json.loads(tool_call["function"]["arguments"])
                    logs.append(f"🔧 LLM选择调用工具: {tool_name}")
                    logs.append(f"🔧 工具参数: {json.dumps(tool_params, ensure_ascii=False)}")
                    
                    # 执行工具
                    tool_result = call_tool(tool_name, tool_params)
                    used_tools.append(tool_name)
                    

                    
                    logs.append(f"🔧 工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}")
                    

                    
                    # 把工具结果返回给LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
            else:
                # 没有工具调用，生成最终内容
                doc_content = llm_response["content"]
                logs.append("✅ 需求分析完成，生成最终文档内容")
                break
        
        if current_round >= max_rounds:
            logs.append("⚠️ 达到最大调用轮次，终止处理")

        # 3. 检查创建文档权限
        logs.append("\n🔐 检查文档创建权限")
        perm_result = call_tool("check_doc_create_permission", {})
        used_tools.append("check_doc_create_permission")
        if not perm_result.get("has_permission", False):
            logs.append("🔐 权限不足，尝试登录lark-cli")
            login_result = call_tool("login_larkcli", {})
            used_tools.append("login_larkcli")
            if not login_result.get("success", False):
                return JSONResponse({
                    "code": 403,
                    "message": "没有文档创建权限，请先完成lark-cli登录授权",
                    "data": {"logs": logs, "used_tools": list(set(used_tools))}
                })

        # 4. 创建飞书文档（最终必须调用）
        logs.append("\n📄 正在创建飞书文档...")
        create_result = call_tool("create_feishu_doc", {
            "title": request.title,
            "content": doc_content
        })
        used_tools.append("create_feishu_doc")
        
        if "error" in create_result:
            logs.append(f"❌ 文档创建失败: {create_result['error']}")
            # 写入失败日志
            write_user_log(
                time_str=time_str,
                title=request.title,
                user_input=request.user_input,
                required_tools=[],
                used_tools=used_tools,
                result="创建失败",
                local_path="",
                doc_url=""
            )
            write_skill_log(time_str, used_tools)
            
            return JSONResponse({
                "code": 500,
                "message": f"文档创建失败: {create_result['error']}",
                "data": {"logs": logs, "used_tools": list(set(used_tools))}
            })
        
        logs.append(f"✅ 文档创建成功!")
        logs.append(f"🔗 文档链接: {create_result['doc_url']}")
        logs.append(f"💾 本地路径: {create_result['local_path']}")

        # 5. 记录日志
        required_tools = []
        
        write_user_log(
            time_str=time_str,
            title=request.title,
            user_input=request.user_input,
            required_tools=required_tools,
            used_tools=used_tools,
            result="创建成功",
            local_path=create_result["local_path"],
            doc_url=create_result["doc_url"]
        )
        write_skill_log(time_str, used_tools)

        # 6. 返回成功响应
        return JSONResponse({
            "code": 200,
            "message": "文档生成成功",
            "data": {
                "title": request.title,
                "doc_url": create_result["doc_url"],
                "local_path": create_result["local_path"],
                "used_tools": list(set(used_tools)),  # 去重
                "logs": logs,
                "rounds": current_round,
                "duration": round(time.time() - start_time, 2)
            }
        })

    except Exception as e:
        logs.append(f"❌ 处理失败: {str(e)}")
        # 写入错误日志
        write_user_log(
            time_str=time_str,
            title=request.title,
            user_input=request.user_input,
            required_tools=[],
            used_tools=used_tools,
            result="处理失败",
            local_path="",
            doc_url=""
        )
        return JSONResponse({
            "code": 500,
            "message": f"处理失败: {str(e)}",
            "data": {"logs": logs, "used_tools": list(set(used_tools))}
        })

# 健康检查接口
@app.get("/Lark-doc-Agent/health")
async def health_check():
    return {"status": "healthy", "service": "Lark-doc-Agent", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=AGENT_CONFIG["host"],
        port=AGENT_CONFIG["port"]
    )