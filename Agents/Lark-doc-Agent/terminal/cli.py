"""
命令行工具 - cli.py
用户可以在命令行中写入提示词，让agent生成飞书文档
"""

import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LLM_CONFIG
from llm import LLMClient
from agent import create_feishu_doc


def main():
    print("=" * 60)
    print("📄 飞书文档助手 - 命令行工具")
    print("=" * 60)

    # 初始化LLM客户端
    llm_client = LLMClient()

    # 系统提示词
    SYSTEM_PROMPT = """你是一个飞书文档助手，可以帮助用户创建和管理飞书文档。
你有以下工具可以使用：
1. create_feishu_doc(title, content) - 创建飞书文档
   - title: 文档标题
   - content: 文档内容（Markdown格式）
   - 返回: 文档ID和URL

重要：如果用户需要创建文档，请先生成内容，然后调用create_feishu_doc工具创建文档。
请保持对话简洁友好。"""

    while True:
        user_input = input("\n请输入需求（输入'exit'退出）: ").strip()
        if user_input.lower() == "exit":
            print("再见！")
            break

        if not user_input:
            continue

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]

            print("\n正在处理...")
            response = llm_client.chat(messages)
            print(f"\n{response}")

        except Exception as e:
            print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    main()
