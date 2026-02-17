"""
TakaneChatModelSimple を使用した簡単なサンプルコード
Simple Chat API（チャットルームなし）を使用したバージョン
"""

from TakaneLLMWrapperSimple import TakaneChatModelSimple
from langchain_core.messages import HumanMessage, AIMessage

import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# TakaneChatModelSimpleのインスタンスを作成
llm = TakaneChatModelSimple(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
    system_prompt="あなたはユーザーの友達です。フレンドリーに応答してください。",
    max_tokens=1024,
    temperature=0.5,
    top_p=1.0,
)

# 単純な質問
print("=== 単純な質問 ===")
messages = [HumanMessage(content="こんにちは！Pythonについて教えてください。")]
result = llm.invoke(messages)
print(f"AI応答: {result.content}\n")

# 会話履歴を含む質問
print("=== 会話履歴を含む質問 ===")
messages = [
    HumanMessage(content="私の名前は太郎です。"),
    AIMessage(content="こんにちは、太郎さん！よろしくお願いします。"),
    HumanMessage(content="私の名前を覚えていますか？"),
]
result = llm.invoke(messages)
print(f"AI応答: {result.content}\n")

# パラメータをカスタマイズした例
print("=== カスタムパラメータでの質問 ===")
llm_creative = TakaneChatModelSimple(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
    system_prompt="あなたは創造的な詩人です。",
    max_tokens=512,
    temperature=0.9,  # より創造的な回答
    top_p=0.95,
)

messages = [HumanMessage(content="冬の朝について短い詩を作ってください。")]
result = llm_creative.invoke(messages)
print(f"AI応答: {result.content}\n")

# 複数ターンの会話
print("=== 複数ターンの会話 ===")
conversation = []

# 1ターン目
conversation.append(
    HumanMessage(content="Pythonのリスト内包表記について教えてください。")
)
result = llm.invoke(conversation)
print(f"ユーザー: {conversation[-1].content}")
print(f"AI: {result.content}\n")
conversation.append(AIMessage(content=result.content))

# 2ターン目
conversation.append(HumanMessage(content="具体的な例を見せてください。"))
result = llm.invoke(conversation)
print(f"ユーザー: {conversation[-1].content}")
print(f"AI: {result.content}\n")
conversation.append(AIMessage(content=result.content))

# 3ターン目
conversation.append(HumanMessage(content="ありがとうございます！"))
result = llm.invoke(conversation)
print(f"ユーザー: {conversation[-1].content}")
print(f"AI: {result.content}\n")

print("=== サンプル実行完了 ===")
