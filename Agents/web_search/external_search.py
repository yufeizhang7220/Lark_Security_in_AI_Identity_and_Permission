"""
外部检索 Agent
负责从外部公开网站获取信息，无权访问任何飞书企业内部数据
"""

from typing import Dict, List, Optional, Any
from base_agent import BaseAgent
import json


class ExternalSearchAgent(BaseAgent):
    """外部检索Agent - 无权访问飞书企业内部数据"""

    def __init__(self):
        super().__init__(
            agent_id="external_search",
            name="外部检索Agent",
            description="负责从外部公开网站获取信息，无权访问任何飞书企业内部数据"
        )
        self.allowed_actions = ["web_search", "fetch_content", "analyze_content"]
        self.blacklisted_resources = [
            "feishu_contacts",
            "feishu_calendar",
            "feishu_datatable",
            "feishu_doc"
        ]

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索任务

        Args:
            task: 任务字典，包含:
                - action: 操作类型 (web_search/fetch_content/analyze_content)
                - params: 操作参数
                - context: 上下文信息
        """
        action = task.get("context", {}).get("action")
        params = task.get("context", {}).get("Agent_data", {}).get("query_data", {})

        if action not in self.allowed_actions:
            self.audit_logger.log_auth_decision(
                decision="DENY",
                caller={"agent_id": self.agent_id, "capabilities": self.get_capabilities()},
                callee="internal_service",
                action=action,
                result="FAILURE",
                error_code="AUTH_003",
                error_message=f"Agent '{self.agent_id}' 没有 '{action}' 权限"
            )
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": f"Agent '{self.agent_id}' 没有 '{action}' 权限",
                "http_status": 403,
                "available_capabilities": self.allowed_actions
            }

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
        执行网络搜索

        Args:
            query: 搜索关键词
            num_results: 返回结果数量

        Returns:
            搜索结果
        """
        task = self.create_request(
            action="web_search",
            params={"query": query, "num_results": num_results}
        )
        return self.execute_task(task)

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        抓取网页内容

        Args:
            url: 网页URL

        Returns:
            网页内容
        """
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
        task = self.create_request(
            action="analyze_content",
            params={"text": text}
        )
        return self.execute_task(task)

    def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行网络搜索（模拟实现）"""
        query = params.get("query", "")
        num_results = params.get("num_results", 5)

        results = [
            {
                "title": f"搜索结果 {i+1} for {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"这是关于 '{query}' 的第 {i+1} 条搜索结果摘要"
            }
            for i in range(num_results)
        ]

        self.audit_logger.log_auth_decision(
            decision="ALLOW",
            caller={"agent_id": self.agent_id, "capabilities": self.get_capabilities()},
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

    def _fetch_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """抓取网页内容（模拟实现）"""
        url = params.get("url", "")

        content = {
            "url": url,
            "title": f"网页标题 - {url}",
            "content": f"这是从 {url} 获取的网页内容...",
            "fetched_at": self._get_current_time()
        }

        self.audit_logger.log_auth_decision(
            decision="ALLOW",
            caller={"agent_id": self.agent_id, "capabilities": self.get_capabilities()},
            callee="internet",
            action="fetch_content",
            result="SUCCESS",
            response_data={"url": url}
        )

        return {
            "success": True,
            "data": content
        }

    def _analyze_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析文本内容（模拟实现）"""
        text = params.get("text", "")

        analysis = {
            "word_count": len(text.split()),
            "char_count": len(text),
            "summary": text[:100] + "..." if len(text) > 100 else text,
            "keywords": self._extract_keywords(text)
        }

        self.audit_logger.log_auth_decision(
            decision="ALLOW",
            caller={"agent_id": self.agent_id, "capabilities": self.get_capabilities()},
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
        return words[:5] if len(words) > 5 else words

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


# 全局实例
external_search_agent = ExternalSearchAgent()
