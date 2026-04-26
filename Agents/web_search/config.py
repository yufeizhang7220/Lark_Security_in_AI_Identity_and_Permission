"""
Agent 身份与权限系统 - 配置文件
定义Agent身份、能力声明、系统参数等核心配置
"""

# ============ 系统基础配置 ============
SYSTEM_NAME = "External Search Agent"
SYSTEM_VERSION = "1.0.0"
DEBUG = True

# ============ JWT 配置 ============
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 60,
    "issuer": "auth-server",
    "audience": "agent-system"
}

# ============ 密钥配置 ============
SECRET_KEY = "external-agent-secret-key-change-in-production-2024"
JWT_SECRET_KEY = "jwt-secret-key-for-agent-auth-2024"

# ============ Agent 身份定义 ============
AGENTS = {
    "external_search": {
        "name": "外部检索Agent",
        "description": "负责从外部公开网站获取信息，无权访问任何飞书企业内部数据",
        "type": "search",
        "static_capabilities": [
            "web_search",
            "fetch_content",
            "analyze_content"
        ],
        "allowed_callers": ["user", "doc_assistant"],
        "max_delegation_depth": 2
    }
}

# ============ Capability 详细定义 ============
CAPABILITIES = {
    "web_search": {
        "description": "执行网络搜索",
        "resource": "internet",
        "action": "search",
        "risk_level": "low"
    },
    "fetch_content": {
        "description": "抓取网页内容",
        "resource": "internet",
        "action": "fetch",
        "risk_level": "medium"
    },
    "analyze_content": {
        "description": "分析网页内容",
        "resource": "internet",
        "action": "analyze",
        "risk_level": "low"
    }
}

# ============ 审计日志配置 ============
AUDIT_CONFIG = {
    "log_all_decisions": True,
    "log_token_issues": True,
    "log_auth_checks": True,
    "log_delegations": True,
    "retention_days": 90,
    "alert_on_high_risk": True
}

# ============ 安全配置 ============
SECURITY_CONFIG = {
    "enable_token_blacklist": True,
    "max_requests_per_minute": 100,
    "rate_limit_window_seconds": 60,
    "allowed_origins": ["*"]
}

# ============ 错误码定义 ============
ERROR_CODES = {
    "AUTH_001": {"message": "Token已过期", "http_status": 401},
    "AUTH_002": {"message": "Token无效或已撤销", "http_status": 401},
    "AUTH_003": {"message": "权限不足", "http_status": 403},
    "AUTH_004": {"message": "Agent未注册", "http_status": 404},
    "AUTH_005": {"message": "越权访问被拦截", "http_status": 403},
    "AUTH_006": {"message": "信任链验证失败", "http_status": 401},
    "SYS_001": {"message": "系统内部错误", "http_status": 500}
}
