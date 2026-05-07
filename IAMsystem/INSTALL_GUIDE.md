# IAMsystem 安装与运行指南

## 一、环境要求
- Python 3.8+
- Windows/Linux/macOS 全平台支持
- 建议内存：256MB以上
- 开放端口：9000、9001、9002、9005、9006

## 二、安装步骤
### 2.1 克隆/下载项目
将IAMsystem目录下载到本地，目录结构如下：
```
IAMsystem/
├── Audit_Traceability/       # 审计追溯模块
├── Delegated_Authorization/  # 委托授权模块
├── Identity_Registration/    # 身份注册模块
├── Admin/                    # 管理后台模块
├── WebPages/                 # 前端页面
├── Storage/                  # 数据存储目录
├── Logs/                     # 日志目录
├── start_all.py              # 一键启动脚本
└── start_all.bat             # Windows一键启动脚本
```

### 2.2 安装依赖
分别进入每个模块目录安装依赖，或使用以下批量安装命令：

#### Windows平台
```powershell
# 安装审计追溯模块依赖
cd Audit_Traceability
pip install -r requirements.txt

# 安装委托授权模块依赖
cd ../Delegated_Authorization
pip install -r requirements.txt

# 安装身份注册模块依赖
cd ../Identity_Registration
pip install -r requirements.txt

# 安装管理后台模块依赖
cd ../Admin
pip install -r requirements.txt

# 返回根目录
cd ..
```

#### Linux/macOS平台
```bash
# 批量安装所有模块依赖
for dir in Audit_Traceability Delegated_Authorization Identity_Registration Admin; do
  cd $dir && pip install -r requirements.txt && cd ..
done
```

### 2.3 配置说明
所有模块的配置文件均在各模块目录下的`config.py`中，可根据需要修改：
- 服务端口配置
- API前缀配置
- JWT密钥配置
- 存储文件路径配置
- 日志路径配置

## 三、运行方式
### 3.1 一键启动（推荐）
#### Windows平台
直接双击运行`start_all.bat`，或在PowerShell中执行：
```powershell
python start_all.py
```

#### Linux/macOS平台
```bash
python3 start_all.py
```

启动成功后会显示所有模块的访问地址：
```
============================================================
IAM系统 一键启动脚本
============================================================
共有 5 个核心模块待启动

✅ 审计追溯模块 启动成功，访问地址: http://localhost:9000
   健康检查: http://localhost:9000/IAMsystem/audit/health
   描述: 负责审计日志记录、异常检测、黑名单管理

✅ 委托授权模块 启动成功，访问地址: http://localhost:9001
   健康检查: http://localhost:9001/IAMsystem/auth/health
   描述: 负责Token签发、校验、撤销，权限委托管理

✅ 身份注册模块 启动成功，访问地址: http://localhost:9002
   健康检查: http://localhost:9002/IAMsystem/identity/health
   描述: 负责用户和Bot身份注册、身份校验

✅ 管理后台模块 启动成功，访问地址: http://localhost:9005
   健康检查: http://localhost:9005/IAMsystem/admin/health
   描述: 负责后台管理、违规记录查询、系统配置

✅ 前端静态服务 启动成功，访问地址: http://localhost:9006
   健康检查: http://localhost:9006/
   描述: 管理前端静态页面服务，访问地址: http://localhost:9006

============================================================
所有模块已启动完成，按 Ctrl+C 停止所有服务
============================================================
```

### 3.2 单模块独立启动
如果需要单独调试某个模块，可以单独启动：
```bash
# 启动审计追溯模块
cd Audit_Traceability && python main.py

# 启动委托授权模块
cd Delegated_Authorization && python main.py

# 启动身份注册模块
cd Identity_Registration && python main.py

# 启动管理后台模块
cd Admin && python main.py

# 启动前端静态服务
cd WebPages && python -m http.server 9006
```

## 四、验证安装
### 4.1 健康检查
访问各模块的健康检查接口，确认服务正常：
```bash
# 审计模块健康检查
curl http://localhost:9000/IAMsystem/audit/health

# 授权模块健康检查
curl http://localhost:9001/IAMsystem/auth/health

# 身份模块健康检查
curl http://localhost:9002/IAMsystem/identity/health
```

正常响应：
```json
{"code":200,"message":"success","data":{"status":"healthy"}}
```

### 4.2 访问管理后台
打开浏览器访问：http://localhost:9006 即可进入管理后台界面。

## 五、常见问题
### 5.1 端口被占用
如果启动时提示端口被占用，可以修改对应模块`config.py`中的`SERVER_PORT`配置，或停止占用端口的进程。

### 5.2 依赖安装失败
如果pip安装依赖失败，可以尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 5.3 日志查看
所有运行日志均存储在`Logs`目录下，按模块分类：
- `Logs/Identity_Registration_Log/`：身份注册模块日志
- `Logs/Delegated_Authorization_Log/`：委托授权模块日志
- `Logs/audit_trail_log/`：审计追溯模块日志

### 5.4 数据存储
所有身份、Token、黑名单数据均存储在`Storage`目录下的JSON文件中，可直接查看或备份。
