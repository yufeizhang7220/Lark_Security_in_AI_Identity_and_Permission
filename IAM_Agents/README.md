# IAM Agents 模块

## 概述

本目录包含飞书AI身份与权限管理系统的所有智能Agent服务，所有Agent均通过IAM系统进行身份认证与权限控制，确保数据访问安全。

## 目录结构

```
IAM_Agents/
├── Agent_indata/          # 企业内部数据Agent
├── Lark-doc-Agent/        # 飞书文档操作Agent
├── web_search/            # 外部公开信息检索Agent
├── start_all.py           # 跨平台一键启动脚本
├── start_all.bat          # Windows一键启动脚本
└── README.md              # 本说明文档
```

## 各Agent说明

### 1. Agent\_indata (企业内部数据Agent)

- **功能**：负责访问和处理企业内部敏感数据
- **端口**：默认 9300
- **核心能力**：
  - 企业内部数据查询与分析
  - 敏感数据访问权限校验
  - 与IAM系统集成实现身份认证
- **技术栈**：FastAPI + Uvicorn + Requests

### 2. Lark-doc-Agent (飞书文档Agent)

- **功能**：提供飞书云文档的全生命周期管理能力
- **端口**：默认 9100
- **核心能力**：
  - 飞书文档创建、读取、更新、删除
  - 文档内容生成与智能编辑
  - 文档权限管理与分享
  - 支持本地文档缓存与同步
- **技术栈**：FastAPI + 火山引擎Ark SDK + 飞书开放API

### 3. web\_search (外部检索Agent)

- **功能**：提供外部公开信息检索服务，无权访问企业内部数据
- **端口**：默认 9200
- **核心能力**：
  - 公开网站内容搜索
  - 网页内容抓取与解析
  - 搜索结果智能分析与整理
  - 与IAM系统集成实现访问控制
- **技术栈**：FastAPI + HTTPX + 外部搜索引擎API

## 前置环境要求

- Python 3.8 及以上版本
- pip 包管理工具
- 必须先启动 [IAMsystem](../IAMsystem/README.md) 服务，所有Agent依赖IAM系统进行身份认证

## 通用配置

所有Agent均支持：

- IAM身份认证集成，所有接口调用需要携带合法IAM令牌
- 日志自动记录与存储
- 跨域请求支持
- 静态资源挂载

## 部署启动

### 方式一：跨平台一键启动（推荐）

1. 进入IAM\_Agents根目录：
   ```bash
   cd e:\CODE\AI_Lark\Lark_Security_in_AI_Identity_and_Permission\IAM_Agents
   ```
2. 执行启动脚本：
   ```bash
   python start_all.py
   ```
3. 启动成功后会显示所有Agent的访问地址、健康检查路径和功能描述

### 方式二：Windows一键启动

1. 进入IAM\_Agents根目录
2. 直接双击运行 `start_all.bat` 即可自动启动所有Agent服务

### 方式三：手动顺序启动

按顺序手动启动所有Agent服务：

1. 启动企业内部数据Agent：
   ```bash
   cd Agent_indata
   pip install -r requirements.txt
   python app.py
   ```
2. 启动飞书文档Agent：
   ```bash
   cd ../Lark-doc-Agent
   pip install -r requirements.txt
   python main.py
   ```
3. 启动外部检索Agent：
   ```bash
   cd ../web_search
   pip install -r requirements.txt
   python server.py
   ```

### 单Agent启动

单独启动某个Agent，进入对应Agent目录执行：

```bash
# 安装依赖
pip install -r requirements.txt
# 启动服务
python main.py  # 或 app.py/server.py，根据Agent入口文件调整
```

## 前端页面说明

### 1. 外部检索Agent前端

- 页面位置：`Lark_Security_in_AI_Identity_and_Permission\IAM_Agents\web_search\templates\index.html`
- 访问地址：**<http://localhost:9200>**
- 功能：外部搜索操作界面，支持输入关键词进行公开信息检索，查看搜索结果和分析内容

### 2. 飞书文档Agent前端

- 页面位置：`e:\CODE\AI_Lark\Lark_Security_in_AI_Identity_and_Permission\IAM_Agents\Lark-doc-Agent\WebPages\index.html`
- 访问地址：**[http://localhost:9100/Lark-doc-Agent/Web](http://localhost:9100/Lark-doc-Agent/Web)**
- 功能：飞书文档操作界面，支持文档创建、内容编辑、权限管理、文档预览等功能

### 3. 企业内部数据Agent

- 无独立前端页面，接口供其他服务调用，通过IAM系统进行访问控制

## 注意事项

- 所有Agent默认仅监听本地地址，生产环境请配置正确的访问权限
- 敏感配置信息请存储在对应目录的`config.py`或专用配置文件中，不要提交到代码仓库
- 所有外部访问均需通过IAM系统认证，禁止直接暴露Agent接口到公网

