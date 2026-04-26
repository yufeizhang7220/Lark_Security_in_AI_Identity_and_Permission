# 飞书文档助手 - Lark-doc-Agent

基于火山引擎自定义模型的飞书文档助手，可以根据用户输入理解需求，调用其他Agent完成企业数据查询和外部信息检索，并将最终报告写入飞书文档。

## 功能特点

- 🤖 **智能理解**：使用火山引擎大模型理解用户需求
- 🔍 **Agent协作**：支持调用企业数据Agent和外部检索Agent
- 📄 **文档创建**：使用lark-cli自动创建飞书文档
- 🎨 **友好界面**：提供Web界面进行文档创建和管理
- 📝 **Markdown支持**：生成的文档支持Markdown格式
- 🔒 **安全认证**：支持飞书API权限控制

## 目录结构

```
Lark-doc-Agent/
├── agent.py              # 主Agent代码
├── config.py             # 配置文件
├── llm.py               # 大模型调用模块
├── requirements.txt      # Python依赖
├── run.py               # 启动脚本
├── README.md            # 使用说明
├── 提示词.md             # 原始需求文档
└── resource/
    ├── docs/            # 文档保存目录
    ├── logs/            # 日志目录
    └── img/             # 图片资源
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API信息

编辑 `config.py` 文件，填入你的火山引擎API信息：

```python
LLM_CONFIG = {
    "api_key": "your_api_key_here",  # 替换为你的API Key
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "your_model_id_here"  # 替换为你的模型ID
}
```

### 3. 启动服务

```bash
python run.py
```

### 4. 访问服务

- **前端界面**: http://localhost:8787/Lark-doc-Agent/main
- **API地址**: http://localhost:8787/Lark-doc-Agent/api/query
- **健康检查**: http://localhost:8787/health

## API使用

### 创建文档

```bash
curl -X POST http://localhost:8787/Lark-doc-Agent/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "创建一个关于公司最新项目进展的报告"
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_input | string | 是 | 用户的文档需求描述 |
| need_enterprise_data | boolean | 否 | 是否需要调用企业数据Agent |
| need_external_search | boolean | 否 | 是否需要调用外部检索Agent |
| enterprise_query_type | string | 否 | 企业数据查询类型 |
| search_keywords | array | 否 | 外部搜索关键词 |

## 工作流程

1. 用户输入文档需求
2. Agent使用大模型理解用户意图
3. Agent智能判断是否需要调用其他Agent
4. 如果需要，调用企业数据Agent或外部检索Agent
5. Agent根据收集到的数据生成报告
6. 使用lark-cli创建飞书文档
7. 返回文档链接给用户

## 日志配置

日志文件保存在 `resource/logs/lark_doc_agent.log`，可在 `config.py` 中修改日志路径：

```python
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "resource/logs/lark_doc_agent.log"
}
```

## 依赖说明

- **fastapi**: Web框架
- **uvicorn**: ASGI服务器
- **pydantic**: 数据验证
- **volcenginesdkarkruntime**: 火山引擎SDK
- **requests**: HTTP请求库

## 注意事项

1. 确保lark-cli已安装并登录
2. 确保火山引擎API配置正确
3. 确保网络连接正常
4. 查看日志文件排查问题

## 常见问题

### lark-cli命令找不到

确保lark-cli在系统PATH中，或在代码中指定完整路径。

### 大模型调用失败

检查API Key和模型ID是否正确配置。

### 文档创建失败

检查lark-cli是否已登录飞书账号。

## License

MIT License
