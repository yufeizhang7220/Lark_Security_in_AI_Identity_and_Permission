"""
LLM模块 - llm.py
火山引擎大模型客户端
"""

from volcenginesdkarkruntime import Ark
from config import LLM_CONFIG


class LLMClient:
    """火山引擎大模型客户端"""

    def __init__(self):
        """初始化LLM客户端"""
        self.client = Ark(
            api_key=LLM_CONFIG["api_key"],
            base_url=LLM_CONFIG["base_url"]
        )
        self.model = LLM_CONFIG["model"]

    def chat(self, messages: list) -> str:
        """调用大模型"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content

    def chat_with_tools(self, messages: list, tools: list) -> dict:
        """调用大模型，支持函数调用"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message

        # 确保消息有role字段
        result = {
            "role": "assistant",
            "content": message.content or ""
        }

        # 检查是否有函数调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                tool_calls.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            result["tool_calls"] = tool_calls

        return result
