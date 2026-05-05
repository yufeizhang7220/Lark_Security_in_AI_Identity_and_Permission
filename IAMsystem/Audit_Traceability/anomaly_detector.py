import time
from typing import Dict, List, Any, Tuple
from logger import AuditLogger
from storage import AuditStorage


class AnomalyDetector:
    def __init__(self):
        self.logger = AuditLogger()
        self.storage = AuditStorage
        self.max_requests_per_hour = 100
        self.max_failed_attempts = 5

    def analyze_requests(self, agent_id: str, ip: str, logs: List[Dict]) -> Tuple[bool, str]:
        now = time.time()
        one_hour_ago = now - 3600

        recent_logs = [
            log for log in logs
            if log.get("timestamp", 0) >= one_hour_ago * 1000
        ]

        agent_logs = [log for log in recent_logs if log.get("agent_id") == agent_id]
        ip_logs = [log for log in recent_logs if log.get("ip") == ip]

        if len(agent_logs) > self.max_requests_per_hour:
            return False, f"Agent {agent_id} 在1小时内请求次数超过{self.max_requests_per_hour}次"

        if len(ip_logs) > self.max_requests_per_hour:
            return False, f"IP {ip} 在1小时内请求次数超过{self.max_requests_per_hour}次"

        failed_attempts = [
            log for log in agent_logs
            if log.get("status") in ["fail", "blocked"]
        ]

        if len(failed_attempts) >= self.max_failed_attempts:
            return False, f"Agent {agent_id} 连续失败次数超过{self.max_failed_attempts}次"

        delegated_chains = [
            log.get("detail", {}).get("delegated_chain")
            for log in agent_logs
            if log.get("detail", {}).get("delegated_chain")
        ]

        for chain in delegated_chains:
            if chain and not self._validate_delegated_chain(chain):
                return False, "委托链权限校验失败"

        return True, "操作合法"

    def _validate_delegated_chain(self, chain: List[Dict]) -> bool:
        if not chain or len(chain) < 1:
            return True

        for i in range(1, len(chain)):
            prev_scope = chain[i-1].get("scope", {})
            curr_scope = chain[i].get("scope", {})

            for resource, actions in curr_scope.items():
                if resource not in prev_scope:
                    return False
                for action in actions:
                    if action not in prev_scope[resource]:
                        return False

        return True

    def detect_anomalies(self, logs: List[Dict]) -> List[Dict]:
        anomalies = []
        agent_activity = {}
        ip_activity = {}

        for log in logs:
            agent_id = log.get("agent_id")
            ip = log.get("ip")
            timestamp = log.get("timestamp", 0)
            status = log.get("status")

            if agent_id not in agent_activity:
                agent_activity[agent_id] = {"requests": 0, "failures": 0, "first_time": timestamp, "ips": set()}
            agent_activity[agent_id]["requests"] += 1
            agent_activity[agent_id]["ips"].add(ip)
            if status in ["fail", "blocked"]:
                agent_activity[agent_id]["failures"] += 1

            if ip not in ip_activity:
                ip_activity[ip] = {"requests": 0, "agents": set()}
            ip_activity[ip]["requests"] += 1
            ip_activity[ip]["agents"].add(agent_id)

        for agent_id, activity in agent_activity.items():
            if activity["failures"] >= self.max_failed_attempts:
                anomalies.append({
                    "type": "brute_force",
                    "agent_id": agent_id,
                    "reason": f"连续失败{activity['failures']}次"
                })

            if len(activity["ips"]) > 5:
                anomalies.append({
                    "type": "异地登录",
                    "agent_id": agent_id,
                    "reason": f"短时间内从{len(activity['ips'])}个不同IP访问"
                })

        for ip, activity in ip_activity.items():
            if activity["requests"] > self.max_requests_per_hour:
                anomalies.append({
                    "type": "请求频率异常",
                    "ip": ip,
                    "reason": f"1小时内请求{activity['requests']}次"
                })

            if len(activity["agents"]) > 20:
                anomalies.append({
                    "type": "IP共享",
                    "ip": ip,
                    "reason": f"{len(activity['agents'])}个不同Agent使用同一IP"
                })

        return anomalies

    def check_audit_legality(self, agent_id: str, start_time: int, end_time: int, operation: str, detail: Dict) -> Tuple[bool, str]:
        if self.storage.is_blacklisted(agent_id=agent_id):
            return False, "Agent已被列入黑名单"

        all_logs = self.logger.export_logs(start_time, end_time)
        
        agent_logs = [
            log for log in all_logs
            if log.get("agent_id") == agent_id and log.get("operation") == operation
        ]

        is_legal, reason = self.analyze_requests(agent_id, detail.get("ip", ""), agent_logs)
        
        if not is_legal:
            self.storage.add_to_blacklist(agent_id=agent_id)
            self.logger.log_blocked(agent_id, detail.get("ip", ""), operation, reason)

        return is_legal, reason