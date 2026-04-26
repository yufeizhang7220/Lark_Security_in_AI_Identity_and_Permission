"""
Agent 基类
所有Agent的基类，定义通用接口和行为
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import uuid
from audit_logger import audit_logger


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.audit_logger = audit_logger

    @abstractmethod
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 任务描述字典，包含:
                - action: 操作类型
                - params: 操作参数
                - context: 上下文信息

        Returns:
            任务执行结果
        """
        pass

    def get_capabilities(self) -> List[str]:
        """获取Agent的能力列表"""
        from config import AGENTS
        return AGENTS.get(self.agent_id, {}).get("static_capabilities", [])

    def create_request(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        query_type: Optional[str] = None,
        output_type: str = "json"
    ) -> Dict[str, Any]:
        """
        创建请求格式

        Args:
            action: 操作类型
            params: 操作参数
            priority: 优先级
            query_type: 查询类型
            output_type: 输出类型

        Returns:
            请求字典
        """
        return {
            "Agent_id": self.agent_id,
            "session_id": f"session_{uuid.uuid4().hex[:8]}",
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "session_datetime": self._get_current_time(),
            "context": {
                "task_type": self._get_task_type(action),
                "action": action,
                "priority": priority,
                "Agent_data": {
                    "query_type": query_type,
                    "output_type": output_type,
                    "query_data": params or {}
                },
                "timeout": 30
            }
        }

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_task_type(self, action: str) -> str:
        """根据action获取任务类型"""
        task_mapping = {
            "web_search": "search",
            "fetch_content": "fetch",
            "analyze_content": "analyze"
        }
        return task_mapping.get(action, "general")

    def log_event(self, event_type: str, description: str, severity: str = "INFO"):
        """记录事件"""
        self.audit_logger.log_security_event(
            event_type=event_type,
            agent_id=self.agent_id,
            description=description,
            severity=severity
        )
