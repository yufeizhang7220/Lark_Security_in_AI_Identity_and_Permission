#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import requests
import json
import os
import sys
from typing import Dict, Any

# 基础配置
BASE_URLS = {
    "audit": "http://localhost:9000/IAMsystem/audit",
    "auth": "http://localhost:9001/IAMsystem/auth",
    "identity": "http://localhost:9002/IAMsystem/identity"
}

@pytest.fixture(scope="session")
def base_headers():
    """基础请求头"""
    return {
        "Content-Type": "application/json"
    }

import uuid
import time
@pytest.fixture(scope="function")
def test_user():
    """测试用用户信息（随机生成名称避免重复）"""
    random_suffix = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
    return {
        "Agent_name": f"测试用户_{random_suffix}",
        "subtype": "user",
        "scope": {
            "doc": ["read", "write"],
            "base": ["read"]
        }
    }

@pytest.fixture(scope="function")
def test_bot():
    """测试用Bot信息（随机生成名称避免重复）"""
    random_suffix = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
    return {
        "Bot_name": f"测试Bot_{random_suffix}",
        "scope": {
            "doc": ["read", "write", "share"],
            "file": ["upload"]
        },
        "api_endpoint": "http://localhost:8000/test/bot"
    }

@pytest.fixture(scope="function")
def registered_user(base_headers, test_user):
    """注册测试用户，返回注册结果（带重试逻辑）"""
    url = f"{BASE_URLS['identity']}/register/user"
    # 最多重试3次，避免名称重复
    for _ in range(3):
        resp = requests.post(url, headers=base_headers, json=test_user)
        if resp.status_code == 201:
            return resp.json()["data"]
        elif "名称已存在" in resp.text:
            # 名称重复，自动生成新名称重试
            random_suffix = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
            test_user["Agent_name"] = f"测试用户_{random_suffix}"
        else:
            break
    assert False, f"测试用户注册失败: {resp.text}"

@pytest.fixture(scope="function")
def registered_bot(base_headers, test_bot):
    """注册测试Bot，返回注册结果（带重试逻辑）"""
    url = f"{BASE_URLS['identity']}/register/bot"
    # 最多重试3次，避免名称重复
    for _ in range(3):
        resp = requests.post(url, headers=base_headers, json=test_bot)
        if resp.status_code == 201:
            return resp.json()["data"]
        elif "名称已存在" in resp.text:
            # 名称重复，自动生成新名称重试
            random_suffix = f"{int(time.time())}_{uuid.uuid4().hex[:4]}"
            test_bot["Bot_name"] = f"测试Bot_{random_suffix}"
        else:
            break
    assert False, f"测试Bot注册失败: {resp.text}"

def get_access_token(agent_id: str, agent_secret: str, scope: Dict = None) -> str:
    """获取测试用AccessToken"""
    url = f"{BASE_URLS['auth']}/apply-token"
    req_data = {
        "agent_id": agent_id,
        "agent_secret": agent_secret,
        "applied_scope": scope or {"doc": ["read"]},
        "ttl": 3600
    }
    resp = requests.post(url, json=req_data)
    if resp.status_code == 200:
        return resp.json()["data"]["access_token"]
    return ""

def add_to_blacklist(agent_id: str = None, ip: str = None):
    """将Agent/IP加入黑名单"""
    url = f"{BASE_URLS['audit']}/blacklist/add"
    params = {}
    if agent_id:
        params["agent_id"] = agent_id
    if ip:
        params["ip"] = ip
    requests.post(url, params=params)

def remove_from_blacklist(agent_id: str = None, ip: str = None):
    """从黑名单移除"""
    url = f"{BASE_URLS['audit']}/blacklist/remove"
    params = {}
    if agent_id:
        params["agent_id"] = agent_id
    if ip:
        params["ip"] = ip
    requests.post(url, params=params)
