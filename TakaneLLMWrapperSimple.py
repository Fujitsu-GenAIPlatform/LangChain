from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, Dict, List, Optional
from pydantic import Field
import requests
import msal
import urllib3


class TakaneChatModelSimple(BaseChatModel):

    tenant_name: str = Field(default="", description="GAPテナント名")
    client_id: str = Field(default="", description="GAPクライアントID")

    model_name: str = Field(
        default="cohere.command-r-plus-fujitsu",
        alias="model",
        description="使用するGAPのモデル名",
    )

    system_prompt: str = Field(
        default="",
        description="毎回ユーザーメッセージに前置きするシステムプロンプト",
    )

    authority: str = Field(
        default="",
        description="GAPの認証用オーソリティURL",
    )
    base_url: str = Field(
        default="",
        description="GAP APIのベースURL",
    )

    token: str = Field(default="", description="GAPのアクセストークン")

    max_tokens: int = Field(default=1024, description="最大トークン数")
    temperature: float = Field(default=0.5, description="予測不可能性（0.0～1.0）")
    top_p: float = Field(default=1.0, description="回答範囲（0.0～1.0）")

    _client: Optional[Any] = None
    _access_token: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "takane_chat_model_simple"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

    def _get_access_token(self) -> str:
        """GAPの認証トークンを取得"""
        if self._access_token:
            return self._access_token

        if not self.authority:
            self.authority = f"https://{self.tenant_name}.b2clogin.com/{self.tenant_name}.onmicrosoft.com/b2c_1_fjcloud_genai_susi"
        if not self.base_url:
            self.base_url = f"https://{self.tenant_name}.generative-ai-platform.cloud.global.fujitsu.com"

        access_token_cache = msal.SerializableTokenCache()
        client = msal.PublicClientApplication(
            self.client_id, authority=self.authority, token_cache=access_token_cache
        )

        result = None
        accounts = client.get_accounts()
        if accounts:
            result = client.acquire_token_silent([], accounts[0])
        else:
            result = client.acquire_token_interactive([], prompt="select_account")

        self._access_token = result["id_token"]
        self._client = client
        return self._access_token

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:

        # response_formatが指定されている場合の処理
        response_format = kwargs.get("response_format")

        # 最新のユーザーメッセージと会話履歴を取得
        question, conversation_history = self._extract_messages(
            messages, response_format
        )

        # アクセストークン取得
        token = self._get_access_token()
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        # Simple Chat APIにリクエスト
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f"{self.base_url}/api/v1/action/defined/text:simple_chat/call"

        body = {
            "max_tokens": self.max_tokens,
            "messages": conversation_history,
            "model": self.model_name,
            "question": question,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        response = requests.post(url, headers=headers, json=body, verify=False)
        response.raise_for_status()

        ai_response = response.json()
        ai_message_content = ai_response.get("answer", "")

        # response_formatが指定されている場合、マークダウンコードブロックを削除
        if response_format and ai_message_content:
            ai_message_content = self._clean_json_response(ai_message_content)

        # ChatResultを作成して返す
        message = AIMessage(content=ai_message_content)
        generation = ChatGeneration(message=message)

        return ChatResult(generations=[generation])

    def _clean_json_response(self, content: str) -> str:
        """
        マークダウンコードブロックを削除してJSONのみを抽出

        Args:
            content: LLMからの応答

        Returns:
            クリーンなJSON文字列
        """
        import re

        # マークダウンコードブロックのパターンにマッチ
        # ```json...``` または ```...``` の形式を検出
        pattern = r"^```(?:json)?\s*\n(.+?)\n```$"
        match = re.search(pattern, content.strip(), re.DOTALL)

        if match:
            # コードブロック内のコンテンツを抽出
            return match.group(1).strip()

        # マークダウンコードブロックがない場合はそのまま返す
        return content.strip()

    def _extract_messages(
        self, messages: List[BaseMessage], response_format: Optional[Any] = None
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        メッセージリストから最新の質問と会話履歴を抽出

        Args:
            messages: メッセージリスト
            response_format: 構造化出力のスキーマ（Pydanticモデル）

        Returns:
            tuple: (最新の質問, 過去の会話履歴)
        """
        conversation_history = []
        question = ""

        # システムプロンプトがある場合は最初のユーザーメッセージに含める
        system_prefix = f"{self.system_prompt}\n\n" if self.system_prompt else ""

        # response_formatが指定されている場合、JSON出力を要求
        if response_format:
            try:
                # Pydanticモデルのスキーマを取得
                schema = response_format.model_json_schema()
                json_instruction = (
                    f"以下のJSONスキーマに厳密に従って、JSONオブジェクトのみを出力してください。\n"
                    f"重要: マークダウンのコードブロック（```json や ```）は使わず、純粋なJSONのみを返してください。\n"
                    f"説明文や追加のテキストは一切含めず、有効なJSONのみを返してください。\n\n"
                    f"スキーマ:\n{schema}\n\n"
                )
                system_prefix = json_instruction + system_prefix
            except Exception:
                # スキーマ取得に失敗した場合は汎用的な指示を追加
                json_instruction = "回答は有効なJSONフォーマットのみで返してください。マークダウンのコードブロックや説明文は含めないでください。\n\n"
                system_prefix = json_instruction + system_prefix

        first_user_message = True

        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                # SystemMessageは次のHumanMessageに含める
                continue
            elif isinstance(msg, HumanMessage):
                content = msg.content
                # 最初のユーザーメッセージの場合はシステムプロンプトを前置き
                if first_user_message and system_prefix:
                    content = f"{system_prefix}{content}"
                    first_user_message = False

                # 最後のメッセージでなければ履歴に追加
                if i < len(messages) - 1:
                    conversation_history.append({"role": "user", "content": content})
                else:
                    # 最後のメッセージは質問として扱う
                    question = content
            elif isinstance(msg, AIMessage):
                conversation_history.append({"role": "ai", "content": msg.content})

        # 最後のメッセージが見つからない場合
        if not question and messages:
            if isinstance(messages[-1], HumanMessage):
                question = messages[-1].content
                if system_prefix and first_user_message:
                    question = f"{system_prefix}{question}"
            else:
                question = messages[-1].content

        return question, conversation_history
