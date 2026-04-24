Agent输入输出的格式

```json
{
  "Agent_id": "源Agent的ID",
  "session_id": "会话id",
  "context": {
    "task_type": "任务类型",		// 过滤敏感信息在这里规定
    "priority": "该命令的权限",
    "Agent_data":{
        "源agent返回的命令或信息",
    },
    "timeout": 30,				//返回截止时间
    "limit_num": 5,				//最大返回数量
    "source": "查询来源",
  },
}
```

