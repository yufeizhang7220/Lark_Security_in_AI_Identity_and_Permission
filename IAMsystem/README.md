# IAM 身份与权限管理系统

## 概述

本系统是飞书AI场景下的企业级身份与权限管理平台，提供身份注册、委托授权、审计追溯三大核心能力，保障AI Agent访问企业数据的安全性与可追溯性。

## 目录结构

```
IAMsystem/
├── API文档/                # 各模块API接口说明文档
├── Admin/                  # 管理后台模块
├── Audit_Traceability/     # 审计追溯模块
├── Delegated_Authorization/ # 委托授权模块
├── Identity_Registration/  # 身份注册模块
├── Logs/                   # 系统运行日志
├── Storage/                # 系统数据存储
├── Test_IAM/               # 系统测试用例
├── WebPages/               # 前端静态页面
├── start_all.bat           # Windows一键启动脚本
└── start_all.py            # 跨平台一键启动脚本
```

## 核心模块说明

| 模块名称   | 端口   | 路径前缀                | 核心功能                                  |
| ------ | ---- | ------------------- | ------------------------------------- |
| 审计追溯模块 | 9000 | /IAMsystem/audit    | 审计日志记录、异常行为检测、访问黑名单管理、操作追溯查询          |
| 委托授权模块 | 9001 | /IAMsystem/auth     | Token签发、Token校验、Token撤销、权限委托管理、权限范围控制 |
| 身份注册模块 | 9002 | /IAMsystem/identity | 用户身份注册、Bot身份注册、身份信息校验、身份状态管理          |
| 管理后台模块 | 9005 | /IAMsystem/admin    | 系统配置管理、违规记录查询、权限审计、系统监控               |
| 前端静态服务 | 9006 | /                   | 管理后台前端页面，访问地址：<http://localhost:9006> |

## 核心能力

### 1. 身份管理

- 支持用户和AI Bot两种身份类型的统一注册与管理
- 身份信息加密存储，支持身份状态的动态管控
- 提供身份校验接口，确保所有访问主体身份合法

### 2. 授权管理

- 基于JWT的令牌机制，支持细粒度权限控制
- 支持临时权限委托，满足跨主体访问场景
- 令牌黑名单机制，支持即时权限回收
- 支持权限范围配置，限制数据访问边界

### 3. 审计追溯

- 全操作行为日志记录，支持完整追溯链路
- 异常行为自动检测与告警
- 访问黑名单自动更新与拦截
- 审计日志多维度查询与统计

## 前置环境要求

- Python 3.8 及以上版本
- pip 包管理工具

## 快速启动

### 方式一：跨平台一键启动（推荐）

1. 进入IAMsystem根目录：
   ```bash
   cd e:\CODE\AI_Lark\Lark_Security_in_AI_Identity_and_Permission\IAMsystem
   ```
2. 执行启动脚本：
   ```bash
   python start_all.py
   ```
3. 启动成功后会显示所有模块的访问地址和健康检查路径

### 方式二：Windows一键启动

1. 进入IAMsystem根目录
2. 直接双击运行 `start_all.bat` 即可自动启动所有模块

### 方式三：单模块启动

如果需要单独启动某个模块，进入对应模块目录，执行：

```bash
# 安装模块依赖
pip install -r requirements.txt
# 启动模块服务
python main.py
```

## 前端页面说明

### 页面位置

前端静态文件存放路径：`Lark_Security_in_AI_Identity_and_Permission\IAMsystem\WebPages`
包含系统管理后台的所有HTML/CSS/JS静态资源。

### 访问方式

服务启动后，访问地址：**<http://localhost:9006>**

### 页面功能

- 身份管理面板：查看和管理所有注册用户与Bot身份信息
- 授权管理面板：查看令牌发放记录、手动撤销权限
- 审计日志面板：查询所有操作审计记录、异常访问统计
- 系统配置面板：调整令牌有效期、异常检测规则等系统参数
- 健康监控面板：实时查看各模块运行状态、接口调用统计

## 健康检查

各模块健康检查地址：

- 审计追溯：<http://localhost:9000/IAMsystem/audit/health>
- 委托授权：<http://localhost:9001/IAMsystem/auth/health>
- 身份注册：<http://localhost:9002/IAMsystem/identity/health>
- 管理后台：<http://localhost:9005/IAMsystem/admin/health>
- 前端页面：<http://localhost:9006/>

## 测试验证

进入 `Test_IAM` 目录，执行测试用例：

```bash
pip install -r requirements.txt
pytest -v
```

测试覆盖正常场景、异常场景、安全场景三类测试用例。

## 配置说明

各模块配置文件位于对应目录下的 `config.py`，可根据实际环境调整：

- 服务端口配置
- 数据库/存储路径配置
- 令牌有效期配置
- 异常检测规则配置
- 日志存储路径配置

## 日志说明

所有运行日志存储在 `Logs` 目录下，按模块和功能分类：

- `Delegated_Authorization_Log/`：授权相关日志（令牌申请、校验、撤销）
- `Identity_Registration_Log/`：身份注册相关日志
- `audit_trail_log/`：审计追溯相关日志

## 数据存储

系统数据存储在 `Storage` 目录下：

- `users.json`：用户身份信息
- `bots.json`：Bot身份信息
- `token_blacklist.json`：令牌黑名单
- `blacklist.json`：访问黑名单
- `token_config.json`：令牌配置参数

## 注意事项

- 生产环境请修改默认配置，尤其是密钥、令牌有效期等安全相关参数
- 日志和存储目录建议定期备份，避免数据丢失
- 所有接口默认支持HTTPS，生产环境请配置SSL证书
- 系统默认监听0.0.0.0，生产环境请配置防火墙限制访问来源

