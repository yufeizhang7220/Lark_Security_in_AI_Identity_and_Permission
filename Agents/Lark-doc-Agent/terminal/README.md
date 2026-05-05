# 飞书文档助手 - 命令行工具

在命令行中输入提示词，让Agent生成飞书文档。

## 功能特点

- 🎯 **命令行交互**：在终端中直接输入文档需求
- 🤖 **智能理解**：使用火山引擎大模型理解用户需求
- 📄 **自动生成**：自动生成结构化的Markdown报告
- 📝 **飞书集成**：使用lark-cli创建飞书文档
- 📊 **详细过程**：显示处理步骤和分析结果

## 目录结构

```
Lark-doc-Agent/
├── terminal/
│   ├── cli.py         # 命令行工具主文件
│   ├── run.sh         # 启动脚本
│   └── README.md       # 使用说明
├── agent.py          # 主Agent代码
├── config.py         # 配置文件
├── llm.py           # 大模型调用模块
└── requirements.txt  # Python依赖
```

## 快速开始

### 1. 配置API信息

编辑 `../config.py` 文件，填入你的火山引擎API信息：

```python
LLM_CONFIG = {
    "api_key": "your_api_key_here",  # 替换为你的API Key
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "your_model_id_here"  # 替换为你的模型ID
}
```

### 2. 运行命令行工具

```bash
# Linux/Mac
sh run.sh

# Windows
python cli.py
```

### 3. 使用方法

1. 启动命令行工具
2. 输入文档需求，例如：
   ```
   请输入文档需求: 创建一个关于公司最新项目进展的报告
   ```
3. 等待Agent处理完成
4. 查看生成的飞书文档链接
5. 输入 `exit` 退出工具

## 示例

```
========================================
📄 飞书文档助手 - 命令行工具
========================================
输入文档需求，按Enter发送，输入'exit'退出
----------------------------------------
✓ 成功初始化LLM客户端

请输入文档需求: 创建一个关于公司最新项目进展的报告

正在处理...
步骤1: 理解用户意图
意图分析: {
  "task_type": "创建报告",
  "domain": "企业内部",
  "document_type": "项目进展报告",
  "key_entities": [],
  "special_requirements": []
}

步骤2: 智能决策
决策结果: {
  "need_enterprise_data": false,
  "enterprise_query_type": "",
  "need_external_search": false,
  "search_keywords": []
}

步骤3: 生成报告
报告生成完成，长度: 1200 字符

报告预览:
# 项目进展报告

## 1. 项目概述
...

步骤4: 创建飞书文档

✓ 文档创建成功！
文档ID: doc_1234567890
文档URL: https://bytedance.larkoffice.com/docx/doc_1234567890
----------------------------------------

请输入文档需求: exit
再见！
```

## 依赖说明

- **volcenginesdkarkruntime**: 火山引擎SDK
- **fastapi**: Web框架（共享依赖）
- **lark-cli**: 飞书文档操作工具

## 注意事项

1. 确保lark-cli已安装并登录
2. 确保火山引擎API配置正确
3. 确保网络连接正常
4. 查看 `../resource/logs` 目录下的日志文件排查问题

## 常见问题

### lark-cli命令找不到
确保lark-cli在系统PATH中，或在代码中指定完整路径。

### 大模型调用失败
检查API Key和模型ID是否正确配置。

### 文档创建失败
检查lark-cli是否已登录飞书账号。
