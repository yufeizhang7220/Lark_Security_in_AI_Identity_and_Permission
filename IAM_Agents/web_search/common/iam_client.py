"""
IAM客户端 - 实现agent对IAM系统的兼容

提供身份注册、验证、权限检查等功能
"""

import requests
import json
import os
import time
from typing import Dict, Any, Optional

class IAMClient:
    """IAM系统客户端"""

    def __init__(self, iam_base_url: str = "http://localhost:9002/IAMsystem/identity"):
        self.iam_base_url = iam_base_url
        self.auth_base_url = "http://localhost:9001/IAMsystem/auth"
        self.audit_base_url = "http://localhost:9000/IAMsystem/audit"
        self.agent_id = None
        self.agent_secret = None
        self.scope = None
        self.access_token = None
        self.token_expire_at = None

    def register_user(self, agent_name: str, subtype: str = "user", 
                      scope: Optional[Dict[str, Any]] = None, ip: str = "127.0.0.1") -> Dict[str, Any]:
        """
        在IAM系统中注册用户身份
        
        Args:
            agent_name: 用户名称
            subtype: 身份类型 (user/visitor)
            scope: 权限范围
            ip: IP地址
            
        Returns:
            注册结果
        """
        if scope is None:
            scope = {"online": ["web_search"]}
            
        data = {
            "Agent_name": agent_name,
            "subtype": subtype,
            "scope": scope,
            "ip": ip
        }
        
        try:
            response = requests.post(
                f"{self.iam_base_url}/register/user",
                json=data
            )
            result = response.json()
            
            if result.get("code") == 201 and "data" in result:
                self.agent_id = result["data"]["agent_id"]
                self.agent_secret = result["data"]["agent_secret"]
                self.scope = result["data"]["scope"]
            
            return result
        except Exception as e:
            return {
                "code": 500,
                "message": f"IAM服务连接失败: {str(e)}",
                "data": None
            }

    def register_bot(self, bot_name: str, scope: Optional[Dict[str, Any]] = None,
                     sub_scope: Optional[Dict[str, Dict[str, Any]]] = None,
                     ip: str = "127.0.0.1", api_endpoint: str = "") -> Dict[str, Any]:
        """
        在IAM系统中注册机器Agent身份
        
        Args:
            bot_name: Bot名称
            scope: Bot自身权限范围
            sub_scope: 不同身份调用该Bot时的权限映射
            ip: IP地址
            api_endpoint: Bot服务地址
            
        Returns:
            注册结果
        """
        if scope is None:
            scope = {"online": ["web_search", "fetch_content"]}
            
        data = {
            "Bot_name": bot_name,
            "scope": scope,
            "sub_scope": sub_scope or {},
            "ip": ip,
            "api_endpoint": api_endpoint
        }
        
        try:
            response = requests.post(
                f"{self.iam_base_url}/register/bot",
                json=data
            )
            result = response.json()
            
            if result.get("code") == 201 and "data" in result:
                self.agent_id = result["data"]["agent_id"]
                self.agent_secret = result["data"]["agent_secret"]
                self.scope = result["data"]["scope"]
            
            return result
        except Exception as e:
            return {
                "code": 500,
                "message": f"IAM服务连接失败: {str(e)}",
                "data": None
            }

    def verify_identity(self, agent_id: Optional[str] = None, 
                        agent_secret: Optional[str] = None) -> Dict[str, Any]:
        """
        验证身份是否有效
        
        Args:
            agent_id: 身份ID
            agent_secret: 身份密钥
            
        Returns:
            验证结果
        """
        if agent_id is None:
            agent_id = self.agent_id
        if agent_secret is None:
            agent_secret = self.agent_secret
            
        if not agent_id or not agent_secret:
            return {
                "code": 400,
                "message": "缺少agent_id或agent_secret",
                "data": None
            }
            
        data = {
            "agent_id": agent_id,
            "agent_secret": agent_secret
        }
        
        try:
            response = requests.post(
                f"{self.iam_base_url}/verify",
                json=data
            )
            return response.json()
        except Exception as e:
            return {
                "code": 500,
                "message": f"IAM服务连接失败: {str(e)}",
                "data": None
            }

    def has_permission(self, permission: str, resource_type: str = "online") -> bool:
        """
        检查是否拥有指定权限
        
        Args:
            permission: 权限名称
            resource_type: 资源类型
            
        Returns:
            是否有权限
        """
        if not self.scope:
            return False
            
        if resource_type in self.scope:
            return permission in self.scope[resource_type]
        return False

    def get_credentials(self) -> Dict[str, Optional[str]]:
        """
        获取当前凭证
        
        Returns:
            包含agent_id和agent_secret的字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_secret": self.agent_secret,
            "scope": self.scope
        }

    def save_credentials_to_file(self, filepath: str) -> bool:
        """
        保存凭证到文件
        
        Args:
            filepath: 凭证文件路径
            
        Returns:
            是否保存成功
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "agent_id": self.agent_id,
                    "agent_secret": self.agent_secret,
                    "scope": self.scope,
                    "access_token": self.access_token,
                    "token_expire_at": self.token_expire_at
                }, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存凭证失败: {e}")
            return False
    
    def load_credentials_from_file(self, filepath: str) -> bool:
        """
        从文件加载凭证
        
        Args:
            filepath: 凭证文件路径
            
        Returns:
            是否加载成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                self.agent_id = creds.get("agent_id")
                self.agent_secret = creds.get("agent_secret")
                self.scope = creds.get("scope")
                self.access_token = creds.get("access_token")
                self.token_expire_at = creds.get("token_expire_at")
            return True
        except Exception as e:
            print(f"加载凭证失败: {e}")
            return False
    
    def apply_access_token(self, applied_scope: Optional[Dict[str, Any]] = None, ttl: int = 3600) -> Dict[str, Any]:
        """
        申请AccessToken
        
        Args:
            applied_scope: 申请的权限范围，默认使用当前scope
            ttl: Token有效期，单位秒
            
        Returns:
            申请结果
        """
        if not self.agent_id or not self.agent_secret:
            return {
                "code": 400,
                "message": "缺少agent_id或agent_secret",
                "data": None
            }
        
        if applied_scope is None:
            applied_scope = self.scope or {}
        
        try:
            response = requests.post(
                f"{self.auth_base_url}/apply-token",
                json={
                    "agent_id": self.agent_id,
                    "agent_secret": self.agent_secret,
                    "applied_scope": applied_scope,
                    "ttl": ttl
                }
            )
            result = response.json()
            
            if result.get("code") == 200 and "data" in result:
                self.access_token = result["data"]["access_token"]
                self.token_expire_at = result["data"]["expire_at"]
            
            return result
        except Exception as e:
            return {
                "code": 500,
                "message": f"授权服务连接失败: {str(e)}",
                "data": None
            }
    
    def verify_access_token(self, access_token: str, required_scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        校验AccessToken合法性
        
        Args:
            access_token: 待校验的AccessToken
            required_scope: 需要的权限范围
            
        Returns:
            校验结果
        """
        print(f"[IAM校验] 开始校验Token，bot_id: {self.agent_id}, required_scope: {required_scope}")
        print(f"[IAM校验] 待校验Token: {access_token[:20]}...")
        
        if not self.agent_id or not self.agent_secret:
            print(f"[IAM校验] 失败：缺少自身身份凭证")
            return {
                "code": 400,
                "message": "缺少agent_id或agent_secret",
                "data": None
            }
        
        try:
            print(f"[IAM校验] 发送请求到IAM服务: {self.auth_base_url}/verify-token")
            response = requests.post(
                f"{self.auth_base_url}/verify-token",
                json={
                    "bot_id": self.agent_id,
                    "agent_secret": self.agent_secret,
                    "access_token": access_token,
                    "required_scope": required_scope
                },
                timeout=10
            )
            print(f"[IAM校验] IAM返回状态码: {response.status_code}")
            result = response.json()
            print(f"[IAM校验] IAM返回结果: {result}")
            return result
        except Exception as e:
            print(f"[IAM校验] 调用IAM服务失败: {str(e)}")
            return {
                "code": 500,
                "message": f"授权服务连接失败: {str(e)}",
                "data": None
            }
    
    def get_valid_access_token(self) -> Optional[str]:
        """
        获取有效的AccessToken，自动刷新过期的Token
        
        Returns:
            有效的AccessToken或None
        """
        # 检查Token是否存在且未过期（提前60秒刷新）
        if self.access_token and self.token_expire_at and (self.token_expire_at - time.time()) > 60:
            return self.access_token
        
        # 申请新Token
        result = self.apply_access_token()
        if result.get("code") == 200:
            return self.access_token
        
        return None
    
    def report_audit_log(self, operation: str, status: str = "success", detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        上报审计日志到IAM系统
        
        Args:
            operation: 操作类型
            status: 操作状态 success/fail/blocked
            detail: 操作详情
            
        Returns:
            上报结果
        """
        if not self.agent_id:
            return {
                "code": 400,
                "message": "缺少agent_id",
                "data": None
            }
        
        try:
            response = requests.post(
                f"{self.audit_base_url}/record",
                json={
                    "agent_id": self.agent_id,
                    "ip": "127.0.0.1",
                    "operation": operation,
                    "status": status,
                    "detail": detail or {}
                }
            )
            return response.json()
        except Exception as e:
            print(f"上报审计日志失败: {e}")
            return {
                "code": 500,
                "message": f"审计服务连接失败: {str(e)}",
                "data": None
            }
