# IAMsystem Request\_Invocation API 使用说明

## 1. 功能概述

`Request_Invocation` API 是 AI身份与权限管理系统（IAMsystem）的核心调用接口，负责统一管理和调度所有注册在系统中的工具Agent。该API提供以下核心功能：

### 1.1 核心能力

| 功能模块        | 描述                                   |
| ----------- | ------------------------------------ |
| **Token验证** | 检查AccessToken的有效性、过期时间、IP绑定          |
| **权限校验**    | 验证请求的操作是否在Token授权范围内，检查整条链路权限        |
| **AI安全检测**  | 使用AI检测请求报文中的违规操作（如提示词突破权限）           |
| **会话追踪**    | 通过SessionID、LastRequire记录对话链路，实现溯源追踪 |
| **请求转发**    | 将合法请求转发至目标工具Agent执行                  |
| **Help帮助**  | 三层结构的帮助系统（工具列表→API列表→API详情）          |

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户/Agent请求                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     IAMsystem Gateway                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Token验证   │→│ 权限校验   │→│ AI安全检测  │→│ 请求转发  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Agent_indata    │ │ External-Search │ │   Other Bots    │
│ (企业数据)      │ │ -Agent(外部检索) │ │   (其他工具)     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

***

## 服务状态检查

```bash
# 健康检查
curl http://localhost:9000/IAMsystem/health

# 响应示例
{
    "status": "healthy",
    "service": "IAMsystem",
    "timestamp": "2026-04-29 10:30:00",
    "registered_bots": 2
}
```

***

## 3. API接口说明

### 3.1 主调用接口

**接口地址**: `POST localhost:9000/IAMsystem/Request_Invocation`

**请求格式**: JSON

**Content-Type**: `application/json`

#### 3.1.1 请求参数

| 字段            | 类型     | 必填 | 说明                                                         |
| ------------- | ------ | -- | ---------------------------------------------------------- |
| task\_type    | string | 是  | 任务类型：`"list_tools"`/`"list_api"`/`"api_detail"`/`"invoke"` |
| query\_bot    | string | 否  | 需要调用的工具Bot名称（task\_type=invoke/list\_api/api\_detail时必填）   |
| API\_ID       | string | 否  | 需要调用的API ID（task\_type=invoke/api\_detail时必填）              |
| AccessToken   | object | 是  | 令牌权限信息                                                     |
| session\_id   | string | 否  | 链路会话ID，首次请求可空，系统自动生成                                       |
| last\_require | string | 否  | 上一次对话ID，用于追踪溯源                                             |
| Agent\_data   | object | 否  | 具体请求数据（task\_type=invoke时必填）                               |
| request\_time | string | 否  | 请求时间，格式：`%Y-%m-%d %H:%M:%S`，系统自动填充                         |
| timeout       | int    | 否  | 超时时间，单位秒，默认30                                              |

#### 3.1.2 AccessToken格式

```json
{
    "token_id": "tk_2e0ead1ba199495682e98001076e8180",
    "AgentID": "Lark-doc-Agent",
    "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
    "scope": {
        "doc": ["read", "write"],
        "tablebase": ["all"],
        "calendar": ["read"],
        "online": ["all"]
    },
    "IP": "127.0.0.1",
    "iat": 1777351882,
    "exp": 1777438282,
    "purpose": "访问企业数据"
}
```

**AccessToken特殊值说明**:

| 字段  | 特殊值       | 含义            |
| --- | --------- | ------------- |
| IP  | `0.0.0.0` | 可变IP，任何IP均可使用 |
| exp | `-1`      | 永久有效，不限时间     |
| exp | Unix时间戳   | 过期时间（秒级）      |

#### 3.1.3 Agent\_data格式

根据不同的目标Bot和API，Agent\_data的格式会有所不同，具体格式由目标Bot的`required_json`定义。

***

## 4. 请求示例

### 4.1 第一层：查看所有工具列表

```json
{
    "task_type": "list_tools",
    "AccessToken": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "scope": {"online": ["all"]},
        "IP": "127.0.0.1",
        "exp": -1
    }
}
```

**响应示例**:

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "tools": [
            {
                "bot_name": "Agent_indata",
                "bot_description": "企业数据 Agent，唯一有权访问飞书通讯录、日历、多维表格。负责查询企业内部数据。"
            },
            {
                "bot_name": "External-Search-Agent",
                "bot_description": "外部检索 Agent，负责从公开网站获取信息，无权访问飞书内部数据。用于搜索网页、抓取公开内容。"
            }
        ],
        "next_step": "使用 task_type='list_api' 和 query_bot='<bot_name>' 查看具体API"
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "request_time": "2026-04-29 10:30:00"
    }
}
```

### 4.2 第二层：查看工具的API列表

```json
{
    "task_type": "list_api",
    "query_bot": "Agent_indata",
    "AccessToken": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "scope": {"online": ["all"]},
        "IP": "127.0.0.1",
        "exp": -1
    },
    "session_id": "sess_abc123",
    "last_require": ""
}
```

**响应示例**:

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "bot_name": "Agent_indata",
        "apis": [
            {
                "api_id": "data_query",
                "description": "负责查询企业内部数据（通讯录、日历、多维表格等）",
                "method": "POST",
                "required_scope": {
                    "doc": ["read"],
                    "tablebase": ["read"],
                    "calendar": ["read"]
                }
            },
            {
                "api_id": "data_health",
                "description": "负责检查服务是否健康",
                "method": "GET",
                "required_scope": {}
            }
        ],
        "next_step": "使用 task_type='api_detail' 和 API_ID='<api_id>' 查看API详情"
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "last_require": "",
        "request_time": "2026-04-29 10:31:00"
    }
}
```

### 4.3 第三层：查看API详情

```json
{
    "task_type": "api_detail",
    "query_bot": "Agent_indata",
    "API_ID": "data_query",
    "AccessToken": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "scope": {"online": ["all"]},
        "IP": "127.0.0.1",
        "exp": -1
    },
    "session_id": "sess_abc123",
    "last_require": "req_001"
}
```

**响应示例**:

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "bot_name": "Agent_indata",
        "api_id": "data_query",
        "api": "localhost:8787/Agent_indata/api/query",
        "description": "负责查询企业内部数据（通讯录、日历、多维表格等）",
        "method": "POST",
        "required_scope": {
            "doc": ["read"],
            "tablebase": ["read"],
            "calendar": ["read"]
        },
        "required_json": {
            "Agent_id": "str 可选的Agent ID",
            "session_id": "str 可选的会话ID",
            "session_datetime": "str 可选的会话时间,格式为%Y-%m-%d_%H:%M:%S",
            "context": {
                "task_type": "str 任务类型，query",
                "priority": "str 优先级，user/bot",
                "Agent_data": {
                    "query_type": "str 查询类型，可选值：Contacts/Calendar/Base",
                    "output_type": "str 输出类型，可选值：json/table/pretty",
                    "query_data": "str 查询内容"
                },
                "timeout": "int 超时时间，单位s"
            }
        },
        "output_json": {
            "Agent_id": "str 可选的Agent ID",
            "session_id": "str 可选的会话ID",
            "session_datetime": "str 可选的会话时间",
            "context": {
                "task_type": "str 任务类型",
                "priority": "str 优先级",
                "Agent_data": {
                    "query_type": "str 查询类型",
                    "output_type": "str 输出类型",
                    "query_data": "str 返回内容"
                },
                "timeout": "int 超时时间"
            }
        }
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "last_require": "req_001",
        "request_time": "2026-04-29 10:32:00"
    }
}
```

### 4.4 调用工具API

```json
{
    "task_type": "invoke",
    "query_bot": "Agent_indata",
    "API_ID": "data_query",
    "AccessToken": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "scope": {
            "doc": ["read"],
            "tablebase": ["read"],
            "calendar": ["read"]
        },
        "IP": "127.0.0.1",
        "iat": 1777351882,
        "exp": 1777438282,
        "purpose": "访问企业数据"
    },
    "session_id": "sess_abc123",
    "last_require": "req_002",
    "Agent_data": {
        "Agent_id": "Lark-doc-Agent",
        "session_id": "sess_abc123",
        "session_datetime": "2026-04-29_10:33:00",
        "context": {
            "task_type": "query",
            "priority": "user",
            "Agent_data": {
                "query_type": "Contacts",
                "output_type": "json",
                "query_data": "搜索姓名包含'张三'的员工"
            },
            "timeout": 30
        }
    },
    "request_time": "2026-04-29 10:33:00",
    "timeout": 30
}
```

**响应示例**:

```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "Agent_id": "Lark-doc-Agent",
        "session_id": "sess_abc123",
        "session_datetime": "2026-04-29_10:33:05",
        "context": {
            "task_type": "query",
            "priority": "user",
            "Agent_data": {
                "query_type": "Contacts",
                "output_type": "json",
                "query_data": [
                    {"姓名": "张三", "部门": "技术部", "职位": "工程师"},
                    {"姓名": "张三丰", "部门": "产品部", "职位": "经理"}
                ]
            },
            "timeout": 30
        }
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "last_require": "req_002",
        "require_id": "req_003",
        "request_time": "2026-04-29 10:33:00",
        "response_time": "2026-04-29 10:33:05",
        "latency_ms": 5000,
        "bot_name": "Agent_indata",
        "api_id": "data_query"
    },
    "audit_info": {
        "token_valid": true,
        "scope_check": "passed",
        "ai_detection": "passed",
        "risk_level": "low"
    }
}
```

***

## 5. IAM调用Bot的请求格式

当IAM系统向目标Bot发送请求时，请求格式如下：

```json
{
    "Agent_indata": {
        "bot_name": "Agent_indata",
        "session_id": "sess_abc123",
        "require_id": "req_001",
        "context": {
            "task_type": "query",
            "priority": "user",
            "Agent_data": {
                "query_type": "Contacts",
                "output_type": "json",
                "query_data": "搜索姓名包含'张三'的员工"
            }
        }
    }
}
```

| 字段          | 类型     | 说明                                           |
| ----------- | ------ | -------------------------------------------- |
| session\_id | string | 整个对话链表的ID，IAM系统生成，贯穿整个对话链路                   |
| require\_id | string | 本次请求的唯一标识，如果Bot需要继续请求IAM，则将last\_require填为此值 |
| context     | object | 具体的请求内容，遵循目标Bot的required\_json格式             |

***

## 6. 验证流程

```
请求进入
    │
    ▼
┌─────────────────────────────┐
│ 1. 请求解析                  │
│    - 提取task_type, query_bot │
│    - 提取AccessToken          │
│    - 生成/验证session_id      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 2. AccessToken验证          │
│    - 验证token_id是否存在     │
│    - 验证AgentSecret         │
│    - 检查IP绑定（IP=0.0.0.0时跳过）│
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 3. 有效期检查               │
│    - exp=-1: 永久有效        │
│    - exp>0: 检查是否过期      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 4. 权限范围验证             │
│    - 查询Bot的API所需权限     │
│    - 验证Token权限是否满足    │
│    - 检查整条链路权限         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 5. AI安全检测               │
│    - 检测请求报文是否违规     │
│    - 检测提示词是否突破权限   │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 6. 会话记录                 │
│    - 生成current_require     │
│    - 更新链路追踪信息         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ 7. 请求转发                 │
│    - 调用目标Bot的API        │
│    - 返回执行结果            │
└─────────────────────────────┘
```

***

## 7. AccessToken 数据存储

### 7.1 存储位置

```
IAMsystem/Storage/TOKENS_table.json
```

### 7.2 数据结构

```json
{
    "tk_2e0ead1ba199495682e98001076e8180": {
        "token_id": "tk_2e0ead1ba199495682e98001076e8180",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "doc": ["read", "write"],
            "tablebase": ["all"],
            "calendar": ["read"],
            "online": ["all"]
        },
        "AgentSecret": "1274f9758bd545cbb08b316588cb0035655c2576",
        "iat": 1777351882,
        "exp": 1777438282,
        "IP": "127.0.0.1",
        "purpose": "访问企业数据"
    },
    "tk_f3449be846bc42c6b734a3e750cd46a2": {
        "token_id": "tk_f3449be846bc42c6b734a3e750cd46a2",
        "AgentID": "Lark-doc-Agent",
        "Subtype": "user",
        "scope": {
            "online": ["all"]
        },
        "AgentSecret": "47058a448425430cb678f47883d315d586cc053e",
        "iat": 1777364339,
        "exp": -1,
        "IP": "0.0.0.0",
        "purpose": "获取企业数据"
    }
}
```

### 7.3 字段说明

| 字段          | 类型     | 说明                            |
| ----------- | ------ | ----------------------------- |
| token\_id   | string | Token唯一标识符，格式：`tk_` + 32位十六进制 |
| AgentID     | string | 关联的Agent标识                    |
| Subtype     | string | 类型：`user` / `system` / `bot`  |
| scope       | object | 权限范围定义                        |
| AgentSecret | string | Agent密钥，用于签名验证（64位十六进制）       |
| iat         | int    | 签发时间（Unix时间戳，秒）               |
| exp         | int    | 过期时间：`-1`永久有效，其他为Unix时间戳      |
| IP          | string | 绑定的客户端IP：`0.0.0.0`允许任意IP      |
| purpose     | string | Token用途描述                     |

### 7.4 权限范围定义

| 权限域       | 描述   | 可用操作                                       |
| --------- | ---- | ------------------------------------------ |
| doc       | 文档访问 | `read`, `write`, `create`, `delete`, `all` |
| tablebase | 多维表格 | `read`, `write`, `append`, `export`, `all` |
| calendar  | 日历会议 | `read`, `write`, `create`, `delete`, `all` |
| online    | 在线服务 | `search`, `get`, `list`, `all`             |

***

## 8. 错误码说明

| 错误码  | 含义            | 处理建议                         |
| ---- | ------------- | ---------------------------- |
| 0    | 成功            | 正常处理                         |
| 1001 | Token不存在      | 检查token\_id是否正确              |
| 1002 | Token已过期      | exp!=-1且当前时间超过exp            |
| 1003 | 权限不足          | Token权限不满足API要求              |
| 1004 | AgentSecret错误 | 检查AgentSecret是否正确            |
| 1005 | IP不匹配         | 当前IP不在允许范围内                  |
| 1006 | 链路权限验证失败      | 下级权限超出上级权限                   |
| 2001 | AI安全检测不通过     | 检测到违规操作或权限突破                 |
| 3001 | Bot未注册        | query\_bot不存在于BOTS\_table    |
| 3002 | API不存在        | API\_ID不存在于Bot的API列表         |
| 3003 | 请求格式错误        | Agent\_data不符合required\_json |
| 9999 | 系统错误          | 联系管理员                        |

### 失败响应示例

**Token过期**:

```json
{
    "code": 1002,
    "msg": "Token已过期",
    "error_detail": {
        "token_id": "tk_f3449be846bc42c6b734a3e750cd46a2",
        "expired_at": "2026-05-02 13:08:59",
        "current_time": "2026-05-03 10:30:00",
        "suggestion": "请重新获取AccessToken"
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "request_time": "2026-05-03 10:30:00"
    }
}
```

**权限不足**:

```json
{
    "code": 1003,
    "msg": "权限不足",
    "error_detail": {
        "token_id": "tk_f3449be846bc42c6b734a3e750cd46a2",
        "required_scope": {"doc": ["read"], "tablebase": ["read"]},
        "available_scope": {"online": ["all"]},
        "suggestion": "当前Token仅拥有online权限，无法访问doc和tablebase资源"
    },
    "trace_info": {
        "session_id": "sess_abc123",
        "request_time": "2026-04-29 10:30:00"
    }
}
```

***

## 9. Help三层结构说明

### 9.1 第一层：工具列表（task\_type=list\_tools）

返回所有已注册的工具Bot名称和简要描述，不包含详细API信息。

### 9.2 第二层：API列表（task\_type=list\_api）

用户选择工具后，返回该工具下所有可用API的列表，包括API ID、描述、方法和所需权限。

### 9.3 第三层：API详情（task\_type=api\_detail）

用户选择具体API后，返回该API的完整信息，包括：

- API地址
- 请求方法
- 所需权限范围
- 请求JSON格式（required\_json）
- 响应JSON格式（output\_json）

***

## 10. 会话追踪机制

### 10.1 追踪字段说明

| 字段             | 说明                         |
| -------------- | -------------------------- |
| session\_id    | 整个对话链表的ID，IAM系统生成，贯穿整个对话链路 |
| last\_require  | 上一次请求的require\_id，用于追踪对话历史 |
| require\_id    | 当前请求的唯一标识，由系统生成            |
| request\_time  | 请求时间戳                      |
| response\_time | 响应时间戳                      |

### 10.2 追踪流程

```
用户首次请求
    │
    ▼
session_id = 生成新ID (如: sess_abc123)
last_require = ""
require_id = req_001
    │
    ▼
用户后续请求
    │
    ▼
session_id = "sess_abc123" (保持不变)
last_require = "req_001" (上一次的require_id)
require_id = req_002
    │
    ▼
IAM调用Bot
    │
    ▼
session_id = "sess_abc123" (传递对话链表ID)
require_id = "req_002" (传递本次请求标识)
    │
    ▼
Bot回调IAM
    │
    ▼
session_id = "sess_abc123" (保持不变)
last_require = "req_002" (IAM上一次发送的require_id)
require_id = req_003
```

***

## 11. 使用注意事项

1. **Token安全性**：AccessToken应妥善保管，避免泄露
2. **权限最小化**：根据实际需求申请最小权限
3. **IP绑定**：生产环境建议绑定固定IP（非0.0.0.0）
4. **有效期管理**：短期Token（exp!=-1）需定期刷新
5. **会话追踪**：保持session\_id不变以维持对话上下文
6. **超时设置**：根据业务需求合理设置timeout参数
7. **日志审计**：所有操作都会记录审计日志，包含完整追踪信息
8. **并发限制**：单个Agent每秒最多10次请求

