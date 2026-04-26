"""
配置文件 - config.py
飞书文档助手配置信息
"""

# 服务配置
AGENT_CONFIG = {
    "name": "Lark-doc-Agent",
    "port": 8787,
    "host": "0.0.0.0"
}

# 火山引擎LLM配置
LLM_CONFIG = {
    "api_key": "ark-68e0d61c-2646-4a0e-8ac1-7ea35da99d21-a6c8f",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-20260423222610-xbx2l"
}

# 其他Agent配置
OTHER_AGENTS = {
    "enterprise_data_agent": {
        "name": "企业数据Agent",
        "agent_id": "Enterprise-Data-Agent",
        "url": "http://localhost:8787/Enterprise-Data-Agent"
    },
    "external_search_agent": {
        "name": "外部检索Agent",
        "agent_id": "External-Search-Agent",
        "url": "http://localhost:8787/External-Search-Agent"
    }
}
