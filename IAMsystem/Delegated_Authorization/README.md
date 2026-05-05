# 委托授权模块使用说明
## 模块功能
实现IAM系统的核心委托授权能力，提供：
1. AccessToken签发（支持动态/静态两种类型）
2. AccessToken合法性校验
3. AccessToken撤销（加入黑名单）
4. 全流程审计日志记录
## 环境要求
- Python 3.10+
## 安装依赖
```bash
cd IAMsystem/Delegated_Authorization
pip install -r requirements.txt
```
## 配置修改
1. 打开`config.py`
2. 修改`JWT_SECRET`为自己的安全密钥，生产环境必须使用复杂随机字符串
3. 如审计接口地址有变化，修改`AUDIT_API_URL`配置
## 启动服务
```bash
python main.py
```
服务默认启动在 `http://0.0.0.0:9001`
## 接口文档
启动后访问自动生成的Swagger文档：`http://localhost:9001/docs`
可以直接在线测试所有接口
## 核心接口测试示例
### 1. 申请AccessToken
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/apply-token" \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "bot_doc_001",
  "agent_secret": "your_agent_secret",
  "applied_scope": {"doc": ["write"], "indata": ["read_bitable"]},
  "purpose": "生成销售报告",
  "ttl": 3600,
  "token_type": "dynamic"
}'
```
### 2. 校验AccessToken
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/verify-token" \
-H "Content-Type: application/json" \
-d '{
  "bot_id": "bot_data_001",
  "agent_secret": "bot_secret",
  "access_token": "your_jwt_token",
  "required_scope": {"indata": ["read_bitable"]}
}'
```
### 3. 撤销AccessToken
```bash
curl -X POST "http://localhost:9001/IAMsystem/auth/revoke-token" \
-H "Content-Type: application/json" \
-d '{
  "agent_id": "bot_doc_001",
  "agent_secret": "your_agent_secret",
  "jti": "token_jti",
  "revoke_reason": "主动撤销"
}'
```
## 日志存储
- 申请Token日志：`../Logs/Delegated_Authorization_Log/Apply_Token/`
- 校验Token日志：`../Logs/Delegated_Authorization_Log/Verify_Token/`
- 撤销Token日志：`../Logs/Delegated_Authorization_Log/Revoke_Token/`
日志按天分片存储，格式为JSON行
## 注意事项
1. 所有agent_secret必须使用bcrypt加密存储，不可明文存储
2. 动态Token最长有效期24小时，静态Token无过期时间但建议仅用于内部服务
3. 审计接口不可用时默认放行，保证核心业务可用性
