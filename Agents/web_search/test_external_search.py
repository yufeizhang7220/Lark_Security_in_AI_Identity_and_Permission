"""
测试外部检索 Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from external_search import external_search_agent
from audit_logger import audit_logger

def test_web_search():
    """测试网络搜索功能"""
    print("=== 测试网络搜索 ===")
    result = external_search_agent.web_search("Python programming", 3)
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"搜索结果数量: {result['total']}")
        for i, item in enumerate(result['results'], 1):
            print(f"结果 {i}: {item['title']}")
            print(f"  URL: {item['url']}")
            print(f"  摘要: {item['snippet']}")
    print()

def test_fetch_url():
    """测试抓取网页内容"""
    print("=== 测试抓取网页内容 ===")
    result = external_search_agent.fetch_url("https://example.com")
    print(f"成功: {result['success']}")
    if result['success']:
        data = result['data']
        print(f"URL: {data['url']}")
        print(f"标题: {data['title']}")
        print(f"内容: {data['content']}")
        print(f"抓取时间: {data['fetched_at']}")
    print()

def test_analyze_text():
    """测试文本分析"""
    print("=== 测试文本分析 ===")
    text = "这是一段测试文本，用于测试外部检索Agent的文本分析功能。"
    result = external_search_agent.analyze_text(text)
    print(f"成功: {result['success']}")
    if result['success']:
        analysis = result['analysis']
        print(f"词数: {analysis['word_count']}")
        print(f"字符数: {analysis['char_count']}")
        print(f"摘要: {analysis['summary']}")
        print(f"关键词: {analysis['keywords']}")
    print()

def test_access_internal_data():
    """测试越权访问（应该被拦截）"""
    print("=== 测试越权访问 ===")
    result = external_search_agent.try_access_internal_data("contacts", "张三")
    print(f"成功: {result['success']}")
    print(f"错误码: {result.get('error_code')}")
    print(f"错误信息: {result.get('error_message')}")
    print()

def test_audit_logs():
    """查看审计日志"""
    print("=== 查看审计日志 ===")
    logs = audit_logger.get_all_logs(limit=10)
    print(f"最近{len(logs)}条审计日志:")
    for log in logs[-5:]:
        print(f"  [{log['timestamp']}] {log['event_type']} - {log.get('decision', 'N/A')}")
        if log.get('error_code'):
            print(f"    错误: {log.get('error_message')}")
    print()

if __name__ == "__main__":
    print("开始测试外部检索 Agent...\n")

    test_web_search()
    test_fetch_url()
    test_analyze_text()
    test_access_internal_data()
    test_audit_logs()

    print("测试完成！")
