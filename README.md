# TakaneChatModel - Langchain Wrapper for Fujitsu GAP

Fujitsu Generative AI Platform (GAP) を Langchain から利用するためのカスタムチャットモデルラッパーです。

## 概要

`TakaneChatModel`および`TakaneChatModelSimple`は、Langchain の BaseChatModel を継承したクラスで、Fujitsu GAP のチャット機能を Langchain のエコシステムに統合します。これにより、Langchain の Chain や Agent などの機能を使用しながら、GAP の LLM モデルを利用できます。

### ラッパークラスの種類

- **TakaneChatModel** (`TakaneLLMWrapper.py`): チャットルーム API を使用したバージョン。会話履歴をサーバー側で管理します。
- **TakaneChatModelSimple** (`TakaneLLMWrapperSimple.py`): Simple Chat API を使用したバージョン。チャットルームを使用せず、クライアント側で会話履歴を管理します。構造化出力（JSON 出力）にも対応しています。

## 動作環境

- Python 3.11 以上
- Langchain 1.1.0

## 必要なパッケージ

```bash
pip install langchain msal requests urllib3 python-dotenv pydantic
```

## ファイル構成

- `TakaneLLMWrapper.py`: チャットルーム API を使用したラッパークラス
- `TakaneLLMWrapperSimple.py`: Simple Chat API を使用したラッパークラス（構造化出力対応）
- `sample_usage.py`: TakaneChatModel の使用例
- `sample_usage_simple.py`: TakaneChatModelSimple の基本的な使用例
- `sample_usage_simple_langgraph.py`: TakaneChatModelSimple と LangGraph を組み合わせた構造化出力の使用例

## 主な機能

### TakaneChatModel（チャットルーム API 版）

- **MSAL 認証**: Azure AD B2C を使用した GAP への認証
- **自動チャットルーム管理**: 未指定の場合は自動的にチャットルームを作成
- **システムプロンプト対応**: 毎回のリクエストにシステムプロンプトを付与
- **サーバー側での会話履歴管理**: GAP アプリ側で会話履歴を保持
- **Langchain 標準インターフェース**: BaseChatModel を継承し、Langchain 標準の使い方に対応

### TakaneChatModelSimple（Simple Chat API 版）

- **MSAL 認証**: Azure AD B2C を使用した GAP への認証
- **チャットルーム不要**: チャットルームを使用せず、シンプルな API 呼び出し
- **クライアント側での会話履歴管理**: メッセージリストとして会話履歴を渡す
- **構造化出力対応**: Pydantic モデルを使用した JSON スキーマベースの構造化出力
- **システムプロンプト対応**: 毎回のリクエストにシステムプロンプトを付与
- **パラメータカスタマイズ**: max_tokens、temperature、top_p などのパラメータを細かく調整可能
- **Langchain 標準インターフェース**: BaseChatModel を継承し、Langchain 標準の使い方に対応

## 使い方

### TakaneChatModel（チャットルーム API 版）の使用例

#### 基本的な使用例

```python
from TakaneLLMWrapper import TakaneChatModel
from langchain_core.messages import HumanMessage

# モデルのインスタンス化
llm = TakaneChatModel(
    tenant_name="your-tenant-name",
    client_id="your-client-id",
    model_name="cohere.command-r-plus-fujitsu",
    system_prompt="あなたは親切なアシスタントです。",
)

# メッセージを送信
messages = [HumanMessage(content="こんにちは！")]
result = llm.invoke(messages)
print(result.content)
```

#### 環境変数を使用した例

`.env`ファイルを作成:

```env
TENANT_NAME=your-tenant-name
CLIENT_ID=your-client-id
CHATROOM_ID=your-chatroom-id
```

Python コード:

```python
from TakaneLLMWrapper import TakaneChatModel
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = TakaneChatModel(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
    chatroom_id=os.getenv("CHATROOM_ID"),
)

messages = [HumanMessage(content="Pythonについて教えてください")]
result = llm.invoke(messages)
print(result.content)
```

詳しい使用例は[sample_usage.py](sample_usage.py)を参照してください。

---

### TakaneChatModelSimple（Simple Chat API 版）の使用例

#### 基本的な使用例

```python
from TakaneLLMWrapperSimple import TakaneChatModelSimple
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

# モデルのインスタンス化
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
messages = [HumanMessage(content="こんにちは！Pythonについて教えてください。")]
result = llm.invoke(messages)
print(result.content)
```

#### 会話履歴を含む使用例

```python
from langchain_core.messages import HumanMessage, AIMessage

# 会話履歴を含む質問
messages = [
    HumanMessage(content="私の名前は太郎です。"),
    AIMessage(content="こんにちは、太郎さん！よろしくお願いします。"),
    HumanMessage(content="私の名前を覚えていますか？"),
]
result = llm.invoke(messages)
print(result.content)
```

#### 構造化出力の使用例（LangGraph との組み合わせ）

```python
from TakaneLLMWrapperSimple import TakaneChatModelSimple
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Dict

# 出力スキーマを定義
class PersonInfo(BaseModel):
    name: str
    age: int

# LLMインスタンスを作成
llm = TakaneChatModelSimple(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
)

# LangGraphで使用
class TestState(TypedDict):
    user_query: str
    person: PersonInfo

def node_chatbot(state: TestState) -> Dict:
    response = llm.invoke(state["user_query"], response_format=PersonInfo)
    person = PersonInfo.model_validate_json(response.content)
    return {"person": person}

graph = StateGraph(TestState)
graph.add_node("chatbot", node_chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

workflow = graph.compile()
final_state = workflow.invoke({"user_query": "太郎は35歳のエンジニアです。"})
print(final_state)
```

詳しい使用例は以下を参照してください：

- [sample_usage_simple.py](sample_usage_simple.py): 基本的な使用例
- [sample_usage_simple_langgraph.py](sample_usage_simple_langgraph.py): LangGraph との組み合わせ例

## パラメータ

### TakaneChatModel（チャットルーム API 版）

#### 必須パラメータ

- `tenant_name` (str): GAP テナント名
- `client_id` (str): GAP クライアント ID

#### オプションパラメータ

- `model_name` (str): 使用する GAP のモデル名（デフォルト: "cohere.command-r-plus-fujitsu"）
- `system_prompt` (str): システムプロンプト（デフォルト: ""）
- `chatroom_id` (str): 使用するチャットルーム ID（未指定の場合は自動作成）
- `authority` (str): 認証用オーソリティ URL（未指定の場合は自動生成）
- `base_url` (str): GAP API のベース URL（未指定の場合は自動生成）
- `token` (str): GAP のアクセストークン（通常は自動取得されるため不要）

### TakaneChatModelSimple（Simple Chat API 版）

#### 必須パラメータ

- `tenant_name` (str): GAP テナント名
- `client_id` (str): GAP クライアント ID

#### オプションパラメータ

- `model_name` (str): 使用する GAP のモデル名（デフォルト: "cohere.command-r-plus-fujitsu"）
- `system_prompt` (str): システムプロンプト（デフォルト: ""）
- `max_tokens` (int): 最大トークン数（デフォルト: 1024）
- `temperature` (float): 予測不可能性（0.0 ～ 1.0、デフォルト: 0.5）
- `top_p` (float): 回答範囲（0.0 ～ 1.0、デフォルト: 1.0）
- `authority` (str): 認証用オーソリティ URL（未指定の場合は自動生成）
- `base_url` (str): GAP API のベース URL（未指定の場合は自動生成）
- `token` (str): GAP のアクセストークン（通常は自動取得されるため不要）

#### invoke メソッドの追加パラメータ

- `response_format` (BaseModel): Pydantic モデルによる構造化出力のスキーマ指定

## 仕組み

### TakaneChatModel（チャットルーム API 版）

1. **認証**: MSAL ライブラリを使用して Azure AD B2C 経由で認証し、アクセストークンを取得
2. **チャットルーム確保**: 指定されたチャットルーム ID を使用、または新規作成
3. **メッセージ送信**: システムプロンプトとユーザーメッセージを結合して GAP API に送信
4. **応答取得**: GAP API から AI の応答を取得して Langchain 形式で返却

### TakaneChatModelSimple（Simple Chat API 版）

1. **認証**: MSAL ライブラリを使用して Azure AD B2C 経由で認証し、アクセストークンを取得
2. **メッセージ処理**: 会話履歴とシステムプロンプトを含めた最新の質問を抽出
3. **構造化出力対応**: `response_format`が指定された場合、Pydantic モデルのスキーマをシステムプロンプトに追加
4. **API 呼び出し**: Simple Chat API にメッセージと会話履歴を送信
5. **応答取得**: GAP API から AI の応答を取得し、必要に応じてマークダウンコードブロックを除去
6. **返却**: Langchain 形式で結果を返却

## 主な違い

| 特徴           | TakaneChatModel        | TakaneChatModelSimple                  |
| -------------- | ---------------------- | -------------------------------------- |
| 使用 API       | チャットルーム API     | Simple Chat API                        |
| チャットルーム | 必要（自動作成可）     | 不要                                   |
| 会話履歴管理   | サーバー側             | クライアント側                         |
| 構造化出力     | 非対応                 | 対応（response_format）                |
| パラメータ調整 | 限定的                 | 詳細（max_tokens, temperature, top_p） |
| 適用場面       | 継続的な会話セッション | 単発の質問、構造化出力が必要な場合     |

## 注意事項

### 共通

- 初回実行時にブラウザが開き、Azure AD B2C の認証画面が表示されます

### TakaneChatModel（チャットルーム API 版）

- チャットルーム ID を指定しない場合、実行の度に新しいチャットルームが作成されます
- 過去の会話履歴は GAP アプリ側で保持しているため最新のユーザーメッセージとシステムプロンプトを付与したメッセージが LLM に送信されます

### TakaneChatModelSimple（Simple Chat API 版）

- チャットルームは使用せず、会話履歴は明示的にメッセージリストとして渡す必要があります
- 構造化出力を使用する場合、Pydantic モデルを定義して `response_format` パラメータで指定してください
- 構造化出力時、LLM がマークダウンコードブロックで囲んだ場合も自動的にクリーンアップされます
