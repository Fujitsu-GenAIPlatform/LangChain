"""
TakaneChatModel を使用した簡単なサンプルコード
"""

from TakaneLLMWrapper import TakaneChatModel
from langchain_core.messages import HumanMessage

import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# TakaneChatModelのインスタンスを作成
llm = TakaneChatModel(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
    system_prompt="あなたはユーザーの友達です。フレンドリーに応答してください。",
    chatroom_id=os.getenv("CHATROOM_ID"),
)

# 単純な質問
print("=== 単純な質問 ===")
messages = [HumanMessage(content="こんにちは！Pythonについて教えてください。")]
result = llm.invoke(messages)
print(f"AI応答: {result.content}\n")
