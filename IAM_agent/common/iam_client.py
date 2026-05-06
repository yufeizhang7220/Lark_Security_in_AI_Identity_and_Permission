"""
IAM客户端 - 实现agent对IAM系统的兼容

提供身份注册、验证、权限检查等功能
"""

import requests
import json
import os
from typing import Dict, Any, Optional

class IAMClient:
    """IAM系统客户端"""

    def __init__(self, iam_base_url: str = "http://localhost:9002/IAMsystem/identity"):
        self.iam_base_url = iam_base_url
        self.agent_id = None
        self.agent_secret = None
        self.scope = None

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
            return True
        except Exception as e:
            print(f"加载凭证失败: {e}")
            return False

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
                    "scope": self.scope
                }, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存凭证失败: {e}")
            return False
