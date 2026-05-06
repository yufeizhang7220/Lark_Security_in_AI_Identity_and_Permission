"""
外部检索 Agent
负责从外部公开网站获取信息，无权访问任何飞书企业内部数据
已兼容IAM系统
"""

from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent
from iam_client import IAMClient
import requests
import json


class ExternalSearchAgent(BaseAgent):
    """外部检索Agent - 无权访问飞书企业内部数据，已兼容IAM"""

    def __init__(self, iam_url: str = "http://localhost:9002/IAMsystem/identity"):
        super().__init__(
            agent_id="external_search",
            name="外部检索Agent",
            description="负责从外部公开网站获取信息，无权访问任何飞书企业内部数据"
        )
        
        # 初始化IAM客户端
        self.iam_client = IAMClient(iam_url)
        self.allowed_actions = ["web_search", "fetch_content", "analyze_content"]
        self.blacklisted_resources = [
            "feishu_contacts",
            "feishu_calendar",
            "feishu_datatable",
            "feishu_doc"
        ]
        
        # 尝试加载凭证或自动注册
        self._initialize_identity()

    def _initialize_identity(self):
        """初始化身份 - 尝试加载凭证或注册新身份"""
        creds_path = os.path.join(os.path.dirname(__file__), "..", "credentials", "external_search.json")
        
        if self.iam_client.load_credentials_from_file(creds_path):
            print(f"✅ 已加载凭证: {self.iam_client.agent_id}")
        else:
            print("🔄 正在注册新身份...")
            result = self.iam_client.register_bot(
                bot_name="ExternalSearchAgent",
                scope={"online": ["web_search", "fetch_content", "analyze_content"]},
                sub_scope={
                    "user": {"online": ["web_search", "fetch_content"]},
                    "visitor": {"online": ["web_search"]}
                },
                api_endpoint="http://localhost:8002/external_search"
            )
            
            if result.get("code") == 201:
                self.iam_client.save_credentials_to_file(creds_path)
                print(f"✅ 注册成功: {self.iam_client.agent_id}")
            else:
                print(f"❌ 注册失败: {result.get('message')}")

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索任务（带IAM身份验证）

        Args:
            task: 任务字典，包含:
                - action: 操作类型 (web_search/fetch_content/analyze_content)
                - params: 操作参数
                - context: 上下文信息
                - agent_id: 调用者身份ID（可选）
                - agent_secret: 调用者密钥（可选）
        """
        action = task.get("context", {}).get("action")
        params = task.get("context", {}).get("Agent_data", {}).get("query_data", {})
        
        # 验证调用者身份（如果提供了凭证）
        caller_agent_id = task.get("agent_id")
        caller_agent_secret = task.get("agent_secret")
        
        if caller_agent_id and caller_agent_secret:
            verify_result = self.iam_client.verify_identity(caller_agent_id, caller_agent_secret)
            if verify_result.get("code") != 200:
                return {
                    "success": False,
                    "error_code": "AUTH_001",
                    "error_message": "调用者身份验证失败",
                    "http_status": 401
                }

        # 验证action是否在允许列表中
        if action not in self.allowed_actions:
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": f"Agent '{self.agent_id}' 没有 '{action}' 权限",
                "http_status": 403,
                "available_capabilities": self.allowed_actions
            }

        # 验证是否尝试访问黑名单资源
        if self._is_accessing_blacklisted_resource(params):
            self.audit_logger.log_auth_decision(
                decision="DENY",
                caller={"agent_id": self.agent_id, "capabilities": self.get_capabilities()},
                callee="internal_service",
                action=action,
                result="FAILURE",
                error_code="AUTH_005",
                error_message="越权访问: 外部检索Agent尝试访问飞书企业内部数据"
            )
            return {
                "success": False,
                "error_code": "AUTH_005",
                "error_message": "越权访问被拦截: 外部检索Agent无权访问飞书企业内部数据",
                "http_status": 403,
                "attempted_resource": "feishu_internal_data"
            }

        # 执行相应的操作
        if action == "web_search":
            return self._web_search(params)
        elif action == "fetch_content":
            return self._fetch_content(params)
        elif action == "analyze_content":
            return self._analyze_content(params)

        return {
            "success": False,
            "error_code": "SYS_001",
            "error_message": f"未知操作: {action}"
        }

    def web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        执行网络搜索（真实实现）

        Args:
            query: 搜索关键词
            num_results: 返回结果数量

        Returns:
            搜索结果
        """
        # 检查权限
        if not self.iam_client.has_permission("web_search", "online"):
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": "没有web_search权限",
                "http_status": 403
            }
            
        task = self.create_request(
            action="web_search",
            params={"query": query, "num_results": num_results}
        )
        return self.execute_task(task)

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        抓取网页内容（真实实现）

        Args:
            url: 网页URL

        Returns:
            网页内容
        """
        # 检查权限
        if not self.iam_client.has_permission("fetch_content", "online"):
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": "没有fetch_content权限",
                "http_status": 403
            }
            
        task = self.create_request(
            action="fetch_content",
            params={"url": url}
        )
        return self.execute_task(task)

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        分析文本内容

        Args:
            text: 要分析的文本

        Returns:
            分析结果
        """
        # 检查权限
        if not self.iam_client.has_permission("analyze_content", "online"):
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": "没有analyze_content权限",
                "http_status": 403
            }
            
        task = self.create_request(
            action="analyze_content",
            params={"text": text}
        )
        return self.execute_task(task)

    def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行网络搜索（真实实现）"""
        query = params.get("query", "")
        num_results = params.get("num_results", 5)

        # 使用真实的网络搜索API
        try:
            # 使用DuckDuckGo搜索API
            search_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json"
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("RelatedTopics", []):
                if "Text" in result and "FirstURL" in result:
                    results.append({
                        "title": result.get("Text", ""),
                        "url": result.get("FirstURL", ""),
                        "snippet": result.get("Text", "")[:200]
                    })
                elif "Topics" in result:
                    for sub_result in result["Topics"]:
                        results.append({
                            "title": sub_result.get("Text", ""),
                            "url": sub_result.get("FirstURL", ""),
                            "snippet": sub_result.get("Text", "")[:200]
                        })
            
            # 限制结果数量
            results = results[:num_results]

            self.audit_logger.log_auth_decision(
                decision="ALLOW",
                caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
                callee="internet",
                action="web_search",
                result="SUCCESS",
                response_data={"num_results": len(results)}
            )

            return {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query
            }
            
        except Exception as e:
            self.audit_logger.log_auth_decision(
                decision="ALLOW",
                caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
                callee="internet",
                action="web_search",
                result="FAILURE",
                error_code="SYS_002",
                error_message=f"搜索失败: {str(e)}"
            )
            
            # 返回模拟结果作为降级
            results = [
                {
                    "title": f"搜索结果 {i+1} for {query}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"这是关于 '{query}' 的第 {i+1} 条搜索结果摘要"
                }
                for i in range(num_results)
            ]
            
            return {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query,
                "warning": "使用模拟数据，网络搜索不可用"
            }

    def _fetch_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """抓取网页内容（真实实现）"""
        url = params.get("url", "")
        
        if not url:
            return {
                "success": False,
                "error_code": "SYS_003",
                "error_message": "缺少URL参数"
            }

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            content = {
                "url": url,
                "title": self._extract_title(response.text),
                "content": response.text[:5000],
                "status_code": response.status_code,
                "fetched_at": self._get_current_time()
            }

            self.audit_logger.log_auth_decision(
                decision="ALLOW",
                caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
                callee="internet",
                action="fetch_content",
                result="SUCCESS",
                response_data={"url": url}
            )

            return {
                "success": True,
                "data": content
            }
            
        except Exception as e:
            self.audit_logger.log_auth_decision(
                decision="ALLOW",
                caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
                callee="internet",
                action="fetch_content",
                result="FAILURE",
                error_code="SYS_002",
                error_message=f"抓取失败: {str(e)}"
            )
            
            # 返回模拟内容作为降级
            content = {
                "url": url,
                "title": f"网页标题 - {url}",
                "content": f"这是从 {url} 获取的网页内容...",
                "fetched_at": self._get_current_time()
            }
            
            return {
                "success": True,
                "data": content,
                "warning": "使用模拟数据，网页抓取不可用"
            }

    def _extract_title(self, html: str) -> str:
        """从HTML中提取标题"""
        import re
        match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "Unknown Title"

    def _analyze_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析文本内容"""
        text = params.get("text", "")

        # 模拟分析结果
        analysis = {
            "word_count": len(text.split()),
            "char_count": len(text),
            "summary": text[:100] + "..." if len(text) > 100 else text,
            "keywords": self._extract_keywords(text)
        }

        self.audit_logger.log_auth_decision(
            decision="ALLOW",
            caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
            callee="internal",
            action="analyze_content",
            result="SUCCESS"
        )

        return {
            "success": True,
            "analysis": analysis
        }

    def _is_accessing_blacklisted_resource(self, params: Dict[str, Any]) -> bool:
        """检查是否尝试访问黑名单资源"""
        params_str = json.dumps(params).lower()
        for resource in self.blacklisted_resources:
            if resource.lower() in params_str:
                return True
        return False

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        words = text.split()
        # 简单返回前5个词作为关键词
        return words[:5] if len(words) > 5 else words

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_iam_credentials(self) -> Dict[str, Any]:
        """获取IAM凭证信息"""
        return self.iam_client.get_credentials()

    def verify_iam_identity(self) -> Dict[str, Any]:
        """验证IAM身份"""
        return self.iam_client.verify_identity()

    def try_access_internal_data(self, data_type: str, query: str) -> Dict[str, Any]:
        """
        尝试访问内部数据（会被拦截）

        Args:
            data_type: 数据类型 (contacts/calendar/datatable)
            query: 查询条件

        Returns:
            访问结果（应该被拦截）
        """
        task = self.create_request(
            action=f"read_{data_type}",
            params={"query": query}
        )
        return self.execute_task(task)


import os
# 全局实例
external_search_agent = ExternalSearchAgent()