## 什么是IAM系统

IAM是一个统筹管理agent之间相互调用的中间系统

## 如何使用IAM系统

### 作为用户agent

1. 注册 IAM 系统，以user或者visitor身份，获取AgentSecret,作为后期申请AccessToken 的凭证
2. 查看 工具列表，获取IAM系统的所有工具和相关API详情
3. 申请 AccessToken， 作为后期调用工具的凭证
4. 调用工具

### 作为bot机器agent

1. 注册IAM系统，以 bot 身份，注册自己信息的相关功能

