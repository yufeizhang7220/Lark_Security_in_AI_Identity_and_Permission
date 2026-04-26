from volcenginesdkarkruntime import Ark

# 初始化客户端（直接用你的密钥）
client = Ark(
    api_key="ark-68e0d61c-2646-4a0e-8ac1-7ea35da99d21-a6c8f",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# 调用大模型
def chat_ai(user_input):
    completion = client.chat.completions.create(
        model="ep-20260423222610-xbx2l",  # 你的模型ID
        messages=[
            {"role": "user", "content": user_input}
        ]
    )
    return completion.choices[0].message.content

# ================== 测试 ==================
if __name__ == "__main__":
    response = chat_ai("你好，你是谁？")
    print("AI 回答：", response)