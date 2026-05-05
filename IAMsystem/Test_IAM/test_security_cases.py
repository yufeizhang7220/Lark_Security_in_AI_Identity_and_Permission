#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全与非法操作测试案例
测试系统的安全拦截能力，所有非法操作应该被正确拦截
"""
import pytest
import requests
import time
from conftest import BASE_URLS, add_to_blacklist, remove_from_blacklist, get_access_token

class TestSecurityCases:
    """安全与非法操作测试"""

    def test_blacklist_ip_block(self, base_headers, test_user):
        """测试IP黑名单拦截"""
        # 将本地IP加入黑名单
        add_to_blacklist(ip="127.0.0.1")
        time.sleep(0.5)
        
        try:
            # 尝试注册用户，应该被拦截
            url = f"{BASE_URLS['identity']}/register/user"
            resp = requests.post(url, headers=base_headers, json=test_user, timeout=5)
            assert resp.status_code == 403, "黑名单IP未被拦截"
            assert "已被拉黑" in resp.text, "拦截提示不正确"
        finally:
            # 清理黑名单
            remove_from_blacklist(ip="127.0.0.1")
            time.sleep(0.5)

    def test_blacklist_agent_block(self, base_headers, registered_user):
        """测试Agent黑名单拦截"""
        agent_id = registered_user["agent_id"]
        add_to_blacklist(agent_id=agent_id)
        time.sleep(0.5)
        
        try:
            # 尝试身份验证，应该被拦截
            url = f"{BASE_URLS['identity']}/verify"
            req_data = {
                "agent_id": agent_id,
                "agent_secret": registered_user["agent_secret"]
            }
            resp = requests.post(url, headers=base_headers, json=req_data, timeout=5)
            assert resp.status_code == 403, "黑名单Agent未被拦截"
            assert "已被拉黑" in resp.text, "拦截提示不正确"
        finally:
            remove_from_blacklist(agent_id=agent_id)
            time.sleep(0.5)

    def test_permission_denied_apply_token(self, base_headers, registered_user):
        """测试申请超出自身权限的Token - 会自动裁剪权限，只返回用户拥有的权限"""
        url = f"{BASE_URLS['auth']}/apply-token"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "applied_scope": {"doc": ["read", "write", "delete"]},  # 用户没有delete权限
            "ttl": 3600
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 200, "申请Token失败"
        granted_scope = resp.json()["data"]["granted_scope"]
        assert "delete" not in granted_scope["doc"], "超出权限的delete未被裁剪"
        assert set(granted_scope["doc"]) == {"read", "write"}, "权限裁剪不正确" # 权限是集合，顺序不影响

    def test_permission_denied_verify_token(self, base_headers, registered_user, registered_bot):
        """测试使用权限不足的Token访问资源 - 应该返回权限不足"""
        # 申请只有read权限的Token
        access_token = get_access_token(
            registered_user["agent_id"],
            registered_user["agent_secret"],
            {"doc": ["read"]}
        )
        
        # 校验需要write权限的操作
        url = f"{BASE_URLS['auth']}/verify-token"
        req_data = {
            "bot_id": registered_bot["agent_id"],
            "agent_secret": registered_bot["agent_secret"],
            "access_token": access_token,
            "required_scope": {"doc": ["write"]}
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 403, "权限不足的Token未被拦截"
        assert "权限不足" in resp.text, "权限不足提示不正确"

    def test_delegated_chain_escalation(self, base_headers, registered_user):
        """测试委托链权限越权 - 下级权限超过上级应该被拦截"""
        # 委托链第二层权限超过第一层，属于越权
        delegated_chain = [
            {"scope": {"doc": ["read"]}},
            {"scope": {"doc": ["read", "write"]}}  # 第二层比第一层多了write权限，越权
        ]
        url = f"{BASE_URLS['auth']}/apply-token"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "delegated_chain": delegated_chain,
            "applied_scope": {"doc": ["write"]},
            "ttl": 3600
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 403, "委托链权限越权未被拦截"

    def test_invalid_agent_secret(self, base_headers, registered_user):
        """测试使用错误密钥 - 应该返回401"""
        url = f"{BASE_URLS['identity']}/verify"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": "wrong_secret_123456"
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 401, "错误密钥未被拦截"
        assert "身份验证失败" in resp.text, "错误提示不正确"

    def test_invalid_token_verify(self, base_headers, registered_bot):
        """测试校验无效Token - 应该返回401"""
        url = f"{BASE_URLS['auth']}/verify-token"
        req_data = {
            "bot_id": registered_bot["agent_id"],
            "agent_secret": registered_bot["agent_secret"],
            "access_token": "invalid_token_abcdefg123456",
            "required_scope": {"doc": ["read"]}
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 401, "无效Token未被拦截"
        assert "无效或已过期" in resp.text, "错误提示不正确"

    def test_revoked_token_verify(self, base_headers, registered_user, registered_bot):
        """测试校验已撤销的Token - 应该返回401"""
        # 申请并撤销Token
        access_token = get_access_token(
            registered_user["agent_id"],
            registered_user["agent_secret"],
            {"doc": ["read"]}
        )
        revoke_url = f"{BASE_URLS['auth']}/revoke-token"
        revoke_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "access_token": access_token,
            "revoke_reason": "测试"
        }
        requests.post(revoke_url, headers=base_headers, json=revoke_data)
        
        # 校验已撤销的Token
        verify_url = f"{BASE_URLS['auth']}/verify-token"
        verify_data = {
            "bot_id": registered_bot["agent_id"],
            "agent_secret": registered_bot["agent_secret"],
            "access_token": access_token,
            "required_scope": {"doc": ["read"]}
        }
        resp = requests.post(verify_url, headers=base_headers, json=verify_data)
        assert resp.status_code == 401, "已撤销的Token未被拦截"
        assert "已被撤销" in resp.text, "错误提示不正确"

    def test_duplicate_registration(self, base_headers, test_user):
        """测试重复注册相同名称的用户/Bot - 应该返回400"""
        # 第一次注册
        url = f"{BASE_URLS['identity']}/register/user"
        requests.post(url, headers=base_headers, json=test_user)
        
        # 第二次注册相同名称
        resp = requests.post(url, headers=base_headers, json=test_user)
        assert resp.status_code == 400, "重复注册未被拦截"
        assert "名称已存在" in resp.text, "错误提示不正确"
