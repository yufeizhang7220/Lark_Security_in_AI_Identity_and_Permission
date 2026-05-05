#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
正常流程测试案例
所有测试用例应该全部通过
"""
import pytest
import requests
from conftest import BASE_URLS, get_access_token

class TestNormalCases:
    """正常流程测试"""
    
    def test_health_check(self, base_headers):
        """测试所有模块健康检查接口"""
        for module, url in BASE_URLS.items():
            resp = requests.get(f"{url}/health", headers=base_headers)
            assert resp.status_code == 200, f"{module}模块健康检查失败"
            assert "healthy" in resp.text or "ok" in resp.text, f"{module}模块健康状态异常"

    def test_user_registration(self, base_headers, test_user):
        """测试正常用户注册"""
        # 先清理已存在的同名用户
        # 注册新用户
        url = f"{BASE_URLS['identity']}/register/user"
        resp = requests.post(url, headers=base_headers, json=test_user)
        # 201创建成功 或 400已存在都算符合预期
        assert resp.status_code in (201, 400), f"用户注册返回异常状态码{resp.status_code}"
        if resp.status_code == 201:
            data = resp.json()["data"]
            assert "agent_id" in data
            assert "agent_secret" in data
            assert data["Agent_name"] == test_user["Agent_name"]

    def test_bot_registration(self, base_headers, test_bot):
        """测试正常Bot注册"""
        url = f"{BASE_URLS['identity']}/register/bot"
        resp = requests.post(url, headers=base_headers, json=test_bot)
        assert resp.status_code in (201, 400), f"Bot注册返回异常状态码{resp.status_code}"
        if resp.status_code == 201:
            data = resp.json()["data"]
            assert "agent_id" in data
            assert "agent_secret" in data
            assert data["Agent_name"] == test_bot["Bot_name"]

    def test_identity_verify(self, base_headers, registered_user):
        """测试正常身份验证"""
        url = f"{BASE_URLS['identity']}/verify"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"]
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 200, "身份验证失败"
        data = resp.json()["data"]
        assert data["valid"] == True
        assert "scope" in data

    def test_apply_token(self, base_headers, registered_user):
        """测试正常申请AccessToken"""
        url = f"{BASE_URLS['auth']}/apply-token"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "applied_scope": {"doc": ["read"]},
            "ttl": 3600
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 200, "Token申请失败"
        data = resp.json()["data"]
        assert "access_token" in data
        assert "granted_scope" in data
        assert data["granted_scope"]["doc"] == ["read"]

    def test_verify_token(self, base_headers, registered_user, registered_bot):
        """测试正常校验AccessToken"""
        # 先申请Token
        access_token = get_access_token(
            registered_user["agent_id"], 
            registered_user["agent_secret"],
            {"doc": ["read"]}
        )
        assert access_token != "", "获取Token失败"
        
        # 校验Token
        url = f"{BASE_URLS['auth']}/verify-token"
        req_data = {
            "bot_id": registered_bot["agent_id"],
            "agent_secret": registered_bot["agent_secret"],
            "access_token": access_token,
            "required_scope": {"doc": ["read"]}
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 200, "Token校验失败"
        data = resp.json()["data"]
        assert data["valid"] == True

    def test_revoke_token(self, base_headers, registered_user):
        """测试正常撤销AccessToken"""
        # 先申请Token
        apply_url = f"{BASE_URLS['auth']}/apply-token"
        apply_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "applied_scope": {"doc": ["read"]},
            "ttl": 3600
        }
        apply_resp = requests.post(apply_url, headers=base_headers, json=apply_data)
        access_token = apply_resp.json()["data"]["access_token"]
        
        # 撤销Token
        revoke_url = f"{BASE_URLS['auth']}/revoke-token"
        revoke_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "access_token": access_token,
            "revoke_reason": "测试撤销"
        }
        revoke_resp = requests.post(revoke_url, headers=base_headers, json=revoke_data)
        assert revoke_resp.status_code == 200, "Token撤销失败"
        
        # 校验已撤销的Token
        verify_url = f"{BASE_URLS['auth']}/verify-token"
        verify_data = {
            "bot_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "access_token": access_token,
            "required_scope": {"doc": ["read"]}
        }
        verify_resp = requests.post(verify_url, headers=base_headers, json=verify_data)
        assert verify_resp.status_code == 401, "已撤销的Token仍能通过校验"

    def test_delegated_chain_normal(self, base_headers, registered_user):
        """测试正常委托链权限校验"""
        # 两层委托链，权限逐层缩小
        delegated_chain = [
            {"scope": {"doc": ["read", "write", "share"], "file": ["upload"]}},
            {"scope": {"doc": ["read", "write"]}}
        ]
        url = f"{BASE_URLS['auth']}/apply-token"
        req_data = {
            "agent_id": registered_user["agent_id"],
            "agent_secret": registered_user["agent_secret"],
            "delegated_chain": delegated_chain,
            "applied_scope": {"doc": ["read"]},
            "ttl": 3600
        }
        resp = requests.post(url, headers=base_headers, json=req_data)
        assert resp.status_code == 200, "正常委托链申请Token失败"
        data = resp.json()["data"]
        assert data["granted_scope"]["doc"] == ["read"]
