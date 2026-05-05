## 各个Agent需要支持的身份

- 飞书文档助手：用户
- 企业数据助手：机器
- 外部检索助手：机器+游客

## 各个身份需要支持的内容

### 用户/游客

1. 完成用户身份 ( **user** / **visitor** ) 注册
2. 妥善保管(内地缓存) agent\_id 和 agent\_secret
3. 申请accesstoken
4. 妥善保管 accesstoken （内地缓存）
5. 若发现 accesstoken 已经过期，及时申请新的 accesstoken
6. 请求调用 其他agent 的时候，在请求头携带 Authorization: Bearer {access\_token}

### 机器

1. 完成机器 ( **bot** ) 注册
2. 妥善保管 （内地保存） bot\_id 和 agent\_secret
3. 获取 accesstoken ，并让 IAM 系统校验 accesstoken （需传入当前操作所需要的权限）

## IAM系统的API文档

详细请见 开发相关\IAM重新开发相关.md、IAMsystem\API文档

## 其他

- 外部检索agent : 需要能尝试拿着游客身份调用企业数据（可以设计一个前端页面）
- 企业数据agent : 需要修改agent，使其能正常使用larkcli查询数据

