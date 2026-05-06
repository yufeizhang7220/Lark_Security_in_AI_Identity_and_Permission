"""
外部检索 Agent
负责从外部公开网站获取信息，无权访问任何飞书企业内部数据
已兼容IAM系统
"""

from typing import Dict, List, Optional, Any
from common.iam_client import IAMClient
import requests
import json
import os


class BaseAgent:
    """基础Agent类"""
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.audit_logger = AuditLogger()
    
    def create_request(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建请求对象"""
        return {
            "context": {
                "action": action,
                "Agent_data": {
                    "query_data": params
                }
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """获取Agent能力列表"""
        return []


class AuditLogger:
    """审计日志类"""
    def log_auth_decision(self, **kwargs):
        """记录审计日志"""
        # 简单实现，打印日志
        print(f"[AUDIT] {kwargs.get('decision')} - {kwargs.get('action')}: {kwargs.get('result', '')}")


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
            print(f"已加载凭证: {self.iam_client.agent_id}")
        else:
            print("正在注册新身份...")
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
                print(f"注册成功: {self.iam_client.agent_id}")
            else:
                print(f"注册失败: {result.get('message')}")

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
        
        # IAM统一权限校验：优先验证AccessToken
        access_token = task.get("access_token")
        if not access_token:
            # 从headers中提取（兼容大小写）
            auth_header = task.get("headers", {}).get("Authorization", "") or task.get("headers", {}).get("authorization", "")
            auth_str = auth_header.strip()
            if auth_str.lower().startswith("bearer "):
                access_token = auth_str[7:].strip()
        
        # 调试日志
        print(f"[业务层] 拿到的AccessToken前缀: {access_token[:20] if access_token else '空'}")
        
        # 拦截空AccessToken
        if not access_token or len(access_token.strip()) == 0 or len(access_token) < 10:
            return {
                "success": False,
                "error_code": "AUTH_001",
                "error_message": "缺少合法的AccessToken，请在请求头携带Authorization: Bearer {access_token}",
                "http_status": 401
            }
        
        # 检查Agent自身是否已完成IAM注册，否则无法进行权限校验
        if not self.iam_client.agent_id or not self.iam_client.agent_secret:
            return {
                "success": False,
                "error_code": "AUTH_002",
                "error_message": "服务未完成IAM注册，暂时不可用",
                "http_status": 503
            }
        
        # 定义各操作需要的权限
        action_permission_map = {
            "web_search": {"online": ["web_search"]},
            "fetch_content": {"online": ["fetch_content"]},
            "analyze_content": {"online": ["analyze_content"]}
        }
        
        # 验证权限
        if action not in action_permission_map:
            return {
                "success": False,
                "error_code": "SYS_001",
                "error_message": f"未知操作: {action}"
            }
            
        required_scope = action_permission_map[action]
        verify_result = self.iam_client.verify_access_token(access_token, required_scope)
        
        if verify_result.get("code") != 200 or not verify_result.get("data", {}).get("valid", False):
            return {
                "success": False,
                "error_code": "AUTH_003",
                "error_message": f"权限验证失败: {verify_result.get('message', '没有对应操作权限')}",
                "http_status": 403
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
        task = self.create_request(
            action="web_search",
            params={"query": query, "num_results": num_results}
        )
        # 获取当前有效AccessToken并注入到任务中
        access_token = self.iam_client.get_valid_access_token()
        if access_token:
            task["access_token"] = access_token
        return self.execute_task(task)

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        抓取网页内容（真实实现）

        Args:
            url: 网页URL

        Returns:
            网页内容
        """
        task = self.create_request(
            action="fetch_content",
            params={"url": url}
        )
        # 获取当前有效AccessToken并注入到任务中
        access_token = self.iam_client.get_valid_access_token()
        if access_token:
            task["access_token"] = access_token
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
        # 获取当前有效AccessToken并注入到任务中
        access_token = self.iam_client.get_valid_access_token()
        if access_token:
            task["access_token"] = access_token
        return self.execute_task(task)

    def _web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行网络搜索（真实实现，国内可用）"""
        query = params.get("query", "")
        num_results = params.get("num_results", 5)
        print(f"[搜索] 开始执行搜索，关键词: {query}, 数量: {num_results}")

        # 使用真实的网络搜索（百度搜索，国内可用）
        try:
            # 尝试导入BeautifulSoup用于解析搜索结果
            from bs4 import BeautifulSoup
            
            # 百度搜索地址
            print(f"[搜索] 调用百度搜索: https://www.baidu.com/s?wd={query}")
            search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(search_url, headers=headers, timeout=5)
            response.raise_for_status()
            print(f"[搜索] 百度搜索返回状态码: {response.status_code}")
            
            # 解析搜索结果
            soup = BeautifulSoup(response.text, 'html.parser')
            result_items = soup.select('div.result.c-container, div.result-op.c-container')
            results = []
            
            for item in result_items[:num_results]:
                try:
                    title_elem = item.select_one('h3 a')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href', '')
                    
                    # 提取摘要
                    snippet_elem = item.select_one('div.c-abstract, span.content-right')
                    snippet = snippet_elem.get_text(strip=True)[:200] if snippet_elem else title
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
                except Exception as e:
                    print(f"[搜索] 解析单条结果失败: {e}")
                    continue
            
            print(f"[搜索] 解析到 {len(results)} 条有效结果")

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
                "query": query,
                "data": {  # 兼容飞书文档助手期望的data字段
                    "search_results": results,
                    "total": len(results),
                    "query": query
                }
            }
            
        except Exception as e:
            print(f"[搜索] 网络搜索失败: {str(e)}")
            self.audit_logger.log_auth_decision(
                decision="ALLOW",
                caller={"agent_id": self.iam_client.agent_id, "capabilities": self.get_capabilities()},
                callee="internet",
                action="web_search",
                result="FAILURE",
                error_code="SYS_002",
                error_message=f"搜索失败: {str(e)}"
            )
            
            # 返回模拟结果作为降级（确保至少有数据返回）
            results = [
                {
                    "title": f"{query} - 搜索结果 {i+1}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"这是关于 '{query}' 的第 {i+1} 条搜索结果，包含相关定义、起源、发展历程和文化影响等内容。"
                }
                for i in range(min(num_results, 5))  # 确保至少返回5条结果
            ]
            print(f"[搜索] 返回模拟结果 {len(results)} 条")
            
            return {
                "success": True,
                "results": results,
                "total": len(results),
                "query": query,
                "warning": "使用模拟数据，网络搜索不可用",
                "data": {  # 兼容飞书文档助手期望的data字段
                    "search_results": results,
                    "total": len(results),
                    "query": query
                }
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


# 全局实例
external_search_agent = ExternalSearchAgent()