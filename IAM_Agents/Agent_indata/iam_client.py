import requests
import json
import os
from typing import Dict, Optional
from config import AGENT_ID, DEFAULT_BOT_SCOPE

IAM_IDENTITY_BASE_URL = "http://localhost:9002/IAMsystem/identity"
IAM_AUTH_BASE_URL = "http://localhost:9001/IAMsystem/auth"
BOT_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "Storage", "bot_credentials.json")

class IAMClient:
    def __init__(self):
        self.bot_id: Optional[str] = None
        self.agent_secret: Optional[str] = None
        self._load_credentials()
        
    def _load_credentials(self):
        if os.path.exists(BOT_CREDENTIALS_PATH):
            with open(BOT_CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.bot_id = data.get("bot_id")
                self.agent_secret = data.get("agent_secret")
    
    def _save_credentials(self, bot_id: str, agent_secret: str):
        os.makedirs(os.path.dirname(BOT_CREDENTIALS_PATH), exist_ok=True)
        with open(BOT_CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "bot_id": bot_id,
                "agent_secret": agent_secret
            }, f, ensure_ascii=False, indent=2)
        self.bot_id = bot_id
        self.agent_secret = agent_secret
    
    def register_bot(self) -> bool:
        if self.bot_id and self.agent_secret:
            return True
        
        try:
            response = requests.post(
                f"{IAM_IDENTITY_BASE_URL}/register/bot",
                json={
                    "Bot_name": AGENT_ID,
                    "scope": DEFAULT_BOT_SCOPE,
                    "api_endpoint": f"http://localhost:{os.getenv('PORT', 9300)}/{AGENT_ID}/api"
                },
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if data.get("code") == 201:
                    bot_data = data.get("data", {})
                    self._save_credentials(bot_data.get("agent_id"), bot_data.get("agent_secret"))
                    return True
            elif response.status_code == 400 and "名称已存在" in response.text:
                return False
        except Exception as e:
            print(f"IAM注册失败: {str(e)}")
            return False
        return False
    
    def verify_access_token(self, access_token: str, required_scope: Dict) -> Dict:
        if not self.bot_id or not self.agent_secret:
            raise Exception("Bot未注册，无法校验Token")
        
        try:
            response = requests.post(
                f"{IAM_AUTH_BASE_URL}/verify-token",
                json={
                    "bot_id": self.bot_id,
                    "agent_secret": self.agent_secret,
                    "access_token": access_token,
                    "required_scope": required_scope
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return data.get("data", {})
            return {
                "valid": False,
                "message": response.json().get("message", "Token校验失败")
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"IAM服务调用失败: {str(e)}"
            }

iam_client = IAMClient()
