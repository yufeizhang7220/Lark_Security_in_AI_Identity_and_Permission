"""
审计日志模块
记录所有授权决策和操作日志，支持查询和追溯
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import AUDIT_CONFIG


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.logs = []
        self.config = AUDIT_CONFIG

    def log_auth_decision(
        self,
        decision: str,
        caller: Dict[str, Any],
        callee: str,
        action: str,
        delegated_user: Optional[str] = None,
        delegation_chain: Optional[List[str]] = None,
        request_context: Optional[Dict] = None,
        result: str = "SUCCESS",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        response_data: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        记录授权决策日志

        Args:
            decision: 决策结果 ALLOW/DENY
            caller: 调用方信息
            callee: 被调用方Agent
            action: 请求的操作
            delegated_user: 委托的用户
            delegation_chain: 信任链
            request_context: 请求上下文
            result: 执行结果
            error_code: 错误码
            error_message: 错误信息
            response_data: 响应数据
            metadata: 元数据

        Returns:
            日志ID
        """

        if not self.config["log_all_decisions"]:
            return None

        log_id = f"log_{uuid.uuid4().hex[:12]}"

        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "event_type": "AUTH_DECISION",
            "decision": decision,
            "caller": caller,
            "callee": callee,
            "action": action,
            "delegated_user": delegated_user,
            "delegation_chain": delegation_chain or [],
            "request_context": request_context or {},
            "result": result,
            "error_code": error_code,
            "error_message": error_message,
            "response_data": response_data,
            "metadata": metadata or {},
            "risk_level": self._calculate_risk_level(action)
        }

        self.logs.append(log_entry)
        self._check_high_risk_alert(log_entry)

        return log_id

    def log_token_issue(
        self,
        agent_id: str,
        token_id: str,
        capabilities: List[str],
        delegated_user: Optional[str] = None,
        delegation_chain: Optional[List[str]] = None,
        issuer: str = "auth-server"
    ) -> str:
        """记录Token签发日志"""
        if not self.config["log_token_issues"]:
            return None

        log_id = f"log_{uuid.uuid4().hex[:12]}"

        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "event_type": "TOKEN_ISSUE",
            "agent_id": agent_id,
            "token_id": token_id,
            "capabilities": capabilities,
            "delegated_user": delegated_user,
            "delegation_chain": delegation_chain or [],
            "issuer": issuer,
            "result": "SUCCESS"
        }

        self.logs.append(log_entry)
        return log_id

    def log_delegation(
        self,
        from_agent: str,
        to_agent: str,
        delegated_capabilities: List[str],
        user_id: str,
        purpose: str,
        result: str = "SUCCESS",
        error_code: Optional[str] = None
    ) -> str:
        """记录委托授权日志"""
        if not self.config["log_delegations"]:
            return None

        log_id = f"log_{uuid.uuid4().hex[:12]}"

        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "event_type": "DELEGATION",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "delegated_capabilities": delegated_capabilities,
            "user_id": user_id,
            "purpose": purpose,
            "result": result,
            "error_code": error_code
        }

        self.logs.append(log_entry)
        return log_id

    def log_security_event(
        self,
        event_type: str,
        agent_id: str,
        description: str,
        severity: str = "WARNING",
        metadata: Optional[Dict] = None
    ) -> str:
        """记录安全事件"""
        log_id = f"log_{uuid.uuid4().hex[:12]}"

        log_entry = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat() + "Z",
            "event_type": f"SECURITY_{event_type}",
            "agent_id": agent_id,
            "description": description,
            "severity": severity,
            "metadata": metadata or {}
        }

        self.logs.append(log_entry)
        return log_id

    def query_logs(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        decision: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询审计日志"""
        results = []

        for log in reversed(self.logs):
            if agent_id and log.get("agent_id") != agent_id and log.get("caller", {}).get("agent_id") != agent_id:
                continue

            if event_type and log.get("event_type") != event_type:
                continue

            if decision and log.get("decision") != decision:
                continue

            if start_time and log.get("timestamp") < start_time:
                continue

            if end_time and log.get("timestamp") > end_time:
                continue

            results.append(log)

            if len(results) >= limit:
                break

        return results

    def get_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取日志"""
        for log in self.logs:
            if log.get("log_id") == log_id:
                return log
        return None

    def get_all_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有日志"""
        return self.logs[-limit:] if limit > 0 else self.logs

    def export_logs(self, format: str = "json") -> str:
        """导出日志"""
        if format == "json":
            return json.dumps(self.logs, indent=2, ensure_ascii=False)
        else:
            if not self.logs:
                return ""

            headers = ["log_id", "timestamp", "event_type", "decision", "agent_id", "action", "result"]
            lines = [",".join(headers)]

            for log in self.logs:
                row = [
                    log.get("log_id", ""),
                    log.get("timestamp", ""),
                    log.get("event_type", ""),
                    log.get("decision", ""),
                    log.get("agent_id", "") or str(log.get("caller", {}).get("agent_id", "")),
                    log.get("action", ""),
                    log.get("result", "")
                ]
                lines.append(",".join(row))

            return "\n".join(lines)

    def _calculate_risk_level(self, action: str) -> str:
        """计算风险等级"""
        high_risk_actions = ["write_contacts", "write_datatable", "delete", "revoke"]
        medium_risk_actions = ["read_contacts", "read_datatable", "write_calendar", "delegate"]

        if action in high_risk_actions:
            return "HIGH"
        elif action in medium_risk_actions:
            return "MEDIUM"
        else:
            return "LOW"

    def _check_high_risk_alert(self, log_entry: Dict[str, Any]):
        """检查高风险操作并告警"""
        if not self.config["alert_on_high_risk"]:
            return

        risk_level = log_entry.get("risk_level", "LOW")
        if risk_level == "HIGH" or log_entry.get("decision") == "DENY":
            print(f"[ALERT] 高风险操作: {log_entry.get('log_id')} - {log_entry.get('action')}")


# 全局审计日志实例
audit_logger = AuditLogger()
