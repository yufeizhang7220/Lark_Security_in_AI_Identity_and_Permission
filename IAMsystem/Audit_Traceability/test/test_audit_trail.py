import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import AuditLogger
from anomaly_detector import AnomalyDetector
from storage import AuditStorage


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.logger = AuditLogger()

    def test_generate_log_id(self):
        log_id = self.logger.generate_log_id()
        self.assertIsNotNone(log_id)
        self.assertEqual(len(log_id), 36)

    def test_get_timestamp_ms(self):
        timestamp = self.logger.get_timestamp_ms()
        self.assertIsInstance(timestamp, int)
        self.assertGreater(timestamp, 1700000000000)

    def test_log(self):
        log_id = self.logger.log(
            agent_id="TestAgent",
            ip="127.0.0.1",
            operation="test",
            status="success",
            detail={"test_key": "test_value"}
        )
        self.assertIsNotNone(log_id)

    def test_log_registration(self):
        log_id = self.logger.log_registration(
            agent_id="TestUser",
            ip="127.0.0.1",
            subtype="user",
            scope={"doc": ["read"]},
            agent_secret_masked="******",
            status="success"
        )
        self.assertIsNotNone(log_id)

    def test_log_authorization(self):
        log_id = self.logger.log_authorization(
            agent_id="TestBot",
            ip="127.0.0.1",
            token_id="test-jti",
            applied_scope={"doc": ["write"]},
            granted_scope={"doc": ["write"]},
            expire_at=1745803600,
            status="success"
        )
        self.assertIsNotNone(log_id)

    def test_log_verification(self):
        log_id = self.logger.log_verification(
            agent_id="TestAgent",
            ip="127.0.0.1",
            token_id="test-jti",
            required_scope={"indata": ["read"]},
            valid=True
        )
        self.assertIsNotNone(log_id)

    def test_log_blocked(self):
        log_id = self.logger.log_blocked(
            agent_id="BadAgent",
            ip="192.168.1.100",
            operation="authorize",
            reason="请求频率异常"
        )
        self.assertIsNotNone(log_id)


class TestAnomalyDetector(unittest.TestCase):
    def setUp(self):
        self.detector = AnomalyDetector()

    def test_validate_delegated_chain_valid(self):
        chain = [
            {"agent_id": "User", "scope": {"doc": ["read", "write"]}},
            {"agent_id": "DocAgent", "scope": {"doc": ["read"]}}
        ]
        result = self.detector._validate_delegated_chain(chain)
        self.assertTrue(result)

    def test_validate_delegated_chain_invalid(self):
        chain = [
            {"agent_id": "User", "scope": {"doc": ["read"]}},
            {"agent_id": "DocAgent", "scope": {"doc": ["read", "write"]}}
        ]
        result = self.detector._validate_delegated_chain(chain)
        self.assertFalse(result)

    def test_analyze_requests_normal(self):
        logs = []
        is_legal, reason = self.detector.analyze_requests("TestAgent", "127.0.0.1", logs)
        self.assertTrue(is_legal)
        self.assertEqual(reason, "操作合法")

    def test_detect_anomalies_no_anomaly(self):
        logs = [
            {"agent_id": "Agent1", "ip": "127.0.0.1", "timestamp": 1745800000000, "status": "success"},
            {"agent_id": "Agent1", "ip": "127.0.0.1", "timestamp": 1745800001000, "status": "success"}
        ]
        anomalies = self.detector.detect_anomalies(logs)
        self.assertEqual(len(anomalies), 0)

    def test_detect_anomalies_brute_force(self):
        logs = []
        for i in range(6):
            logs.append({
                "agent_id": "BadAgent",
                "ip": "127.0.0.1",
                "timestamp": 1745800000000 + i * 1000,
                "status": "fail"
            })
        anomalies = self.detector.detect_anomalies(logs)
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "brute_force")


class TestAuditStorage(unittest.TestCase):
    def setUp(self):
        self.storage = AuditStorage

    def test_load_blacklist(self):
        blacklist = self.storage.load_blacklist()
        self.assertIsInstance(blacklist, dict)
        self.assertIn("agents", blacklist)
        self.assertIn("ips", blacklist)
        self.assertIn("users", blacklist)

    def test_add_and_check_blacklist(self):
        test_agent = "TestAgentForBlacklist"
        test_ip = "192.168.1.200"

        self.storage.add_to_blacklist(agent_id=test_agent, ip=test_ip)

        is_agent_blacklisted = self.storage.is_blacklisted(agent_id=test_agent)
        is_ip_blacklisted = self.storage.is_blacklisted(ip=test_ip)

        self.assertTrue(is_agent_blacklisted)
        self.assertTrue(is_ip_blacklisted)

        blacklist = self.storage.load_blacklist()
        if test_agent in blacklist["agents"]:
            blacklist["agents"].remove(test_agent)
        if test_ip in blacklist["ips"]:
            blacklist["ips"].remove(test_ip)
        self.storage.save_blacklist(blacklist)

    def test_is_blacklisted_not_in_list(self):
        result = self.storage.is_blacklisted(agent_id="NonExistentAgent")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
