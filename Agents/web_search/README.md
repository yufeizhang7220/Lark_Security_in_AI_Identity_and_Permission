# 外部检索 Agent

## 项目概述

外部检索Agent是一个独立的AI Agent实现，专门负责从外部公开网站获取信息。该Agent无权访问任何飞书企业内部数据，具备完整的安全防护机制。

## 核心功能

- **网络搜索** (`web_search`): 执行网络搜索查询
- **网页抓取** (`fetch_content`): 抓取指定URL的网页内容
- **文本分析** (`analyze_content`): 分析和提取文本关键信息

## 安全特性

- 细粒度权限控制
- 黑名单资源访问拦截
- 完整审计日志记录
- 越权访问实时拦截

## 权限限制

外部检索Agent**只能**执行以下操作：
- `web_search` - 网络搜索
- `fetch_content` - 网页抓取
- `analyze_content` - 文本分析

**禁止访问**以下飞书内部资源：
- `feishu_contacts` - 通讯录
- `feishu_calendar` - 日历
- `feishu_datatable` - 多维表格
- `feishu_doc` - 文档

## 项目结构

```
external_search_agent/
├── base_agent.py           # Agent基类
├── external_search.py      # 外部检索Agent实现
├── config.py               # 配置文件
├── audit_logger.py         # 审计日志
├── test_external_search.py # 测试脚本
└── requirements.txt        # 依赖
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行测试

```bash
python test_external_search.py
```

## 使用示例

```python
from external_search import external_search_agent

# 网络搜索
result = external_search_agent.web_search("Python教程", 5)
print(result)

# 抓取网页
result = external_search_agent.fetch_url("https://example.com")
print(result)

# 文本分析
result = external_search_agent.analyze_text("这是一段测试文本")
print(result)

# 尝试越权访问（会被拦截）
result = external_search_agent.try_access_internal_data("contacts", "张三")
print(result)  # 返回错误信息
```

## 请求格式

```json
{
    "Agent_id": "external_search",
    "session_id": "会话ID",
    "request_id": "请求ID",
    "session_datetime": "发送时间",
    "context": {
        "task_type": "任务类型",
        "action": "web_search/fetch_content/analyze_content",
        "priority": "优先级",
        "Agent_data": {
            "query_type": "查询类型",
            "output_type": "输出类型",
            "query_data": {}
        },
        "timeout": 30
    }
}
```

## 审计日志

系统会自动记录所有操作：
- 授权决策（允许/拒绝）
- 操作结果
- 错误信息
- 时间戳

查看日志：
```python
from audit_logger import audit_logger
logs = audit_logger.get_all_logs(limit=100)
```

## 错误码

| 错误码 | 说明 | HTTP状态 |
|--------|------|----------|
| AUTH_003 | 权限不足 | 403 |
| AUTH_005 | 越权访问被拦截 | 403 |
| SYS_001 | 系统内部错误 | 500 |
