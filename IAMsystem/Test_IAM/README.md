# IAM系统测试用例集
## 📋 测试覆盖范围
### 1. 正常流程测试 (`test_normal_cases.py`)
- ✅ 所有模块健康检查
- ✅ 用户/Bot正常注册
- ✅ 身份正常验证
- ✅ AccessToken正常申请、校验、撤销
- ✅ 合法委托链权限校验
### 2. 安全与非法操作测试 (`test_security_cases.py`)
- ✅ IP黑名单拦截
- ✅ Agent黑名单拦截
- ✅ 超出权限申请Token拦截
- ✅ 权限不足Token访问拦截
- ✅ 委托链权限越权拦截
- ✅ 错误密钥/无效Token拦截
- ✅ 已撤销Token拦截
- ✅ 重复注册拦截
### 3. 异常场景与兜底策略测试 (`test_exception_cases.py`)
- ✅ 审计接口不可用时的兜底策略（默认放行，不影响业务）
- ✅ 请求频率超限拦截和自动拉黑
- ✅ 连续失败次数过多自动拉黑
- ✅ 请求超时处理
- ✅ 无效参数/格式错误处理
- ✅ 特殊字符输入处理（防注入）
- ✅ 超大权限请求处理
- ✅ 空委托链处理
- ✅ 越权撤销他人Token拦截
---
## 🚀 运行方法
### 前置准备
1. 先启动所有IAM服务：在IAMsystem目录下运行`python start_all.py`
2. 安装测试依赖：在当前Test_IAM目录下执行：
   ```bash
   pip install -r requirements.txt
   ```
### 运行测试
```bash
# 运行所有测试
pytest -v
# 只运行正常流程测试
pytest test_normal_cases.py -v
# 只运行安全测试
pytest test_security_cases.py -v
# 只运行异常场景测试
pytest test_exception_cases.py -v
# 生成测试报告
pytest -v --html=report.html
```
---
## 📌 注意事项
1. 测试会自动创建测试用户和Bot，不会影响现有数据
2. 黑名单相关测试会自动清理测试数据，不会污染正式黑名单
3. 频率限制和连续失败测试可能会导致测试用Agent被临时拉黑，测试结束后会自动释放
4. 运行测试前请确保所有三个模块服务都已正常启动
---
## 🎯 预期结果
所有测试用例应该全部通过，如果有失败的用例，说明对应功能存在bug，需要修复。
