"""
测试Agent与IAM系统的兼容性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from external_search.main import ExternalSearchAgent

def test_iam_compatibility():
    """测试IAM兼容性"""
    print("=== 测试Agent与IAM系统兼容性 ===")
    
    # 创建Agent实例（会自动注册到IAM）
    print("\n1. 创建外部检索Agent...")
    agent = ExternalSearchAgent()
    
    # 获取IAM凭证
    print("\n2. 获取IAM凭证...")
    credentials = agent.get_iam_credentials()
    print(f"   agent_id: {credentials.get('agent_id')}")
    print(f"   agent_secret: {credentials.get('agent_secret')[:10]}...")
    print(f"   scope: {credentials.get('scope')}")
    
    # 验证身份
    print("\n3. 验证IAM身份...")
    verify_result = agent.verify_iam_identity()
    print(f"   验证结果: {verify_result}")
    
    # 测试网络搜索
    print("\n4. 测试网络搜索功能...")
    search_result = agent.web_search("Python FastAPI", num_results=3)
    print(f"   搜索成功: {search_result.get('success')}")
    if search_result.get("results"):
        for i, result in enumerate(search_result["results"], 1):
            print(f"   结果{i}: {result.get('title')[:50]}...")
    
    # 测试网页抓取
    print("\n5. 测试网页抓取功能...")
    fetch_result = agent.fetch_url("https://www.example.com")
    print(f"   抓取成功: {fetch_result.get('success')}")
    if fetch_result.get("data"):
        print(f"   标题: {fetch_result['data'].get('title')}")
    
    # 测试文本分析
    print("\n6. 测试文本分析功能...")
    analyze_result = agent.analyze_text("这是一段测试文本，用于测试文本分析功能。")
    print(f"   分析成功: {analyze_result.get('success')}")
    if analyze_result.get("analysis"):
        print(f"   词数: {analyze_result['analysis'].get('word_count')}")
        print(f"   关键词: {analyze_result['analysis'].get('keywords')}")
    
    # 测试越权拦截
    print("\n7. 测试越权访问拦截...")
    hack_result = agent.try_access_internal_data("feishu_contacts", "查询员工信息")
    print(f"   越权拦截成功: {not hack_result.get('success')}")
    print(f"   错误信息: {hack_result.get('error_message')}")
    
    print("\n=== IAM兼容性测试完成 ===")

if __name__ == "__main__":
    test_iam_compatibility()