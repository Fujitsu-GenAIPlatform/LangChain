from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, Dict, List, Optional
from pydantic import Field
import requests
import msal
import urllib3


class TakaneChatModel(BaseChatModel):

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

    chatroom_id: str = Field(default="", description="使用するGAPのチャットルームID")
    token: str = Field(default="", description="GAPのアクセストークン")

    _client: Optional[Any] = None
    _access_token: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    @property
    def _llm_type(self) -> str:
        return "takane_chat_model"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
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

    def _ensure_chatroom(self) -> str:
        """チャットルームIDを確保(未設定の場合は新規作成)"""
        if self.chatroom_id:
            return self.chatroom_id

        # 新規チャットルーム作成
        token = self._get_access_token()
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        url = f"{self.base_url}/api/v1/chats"
        body = {
            "name": f"Langchain Chat - {self.model_name}",
            "chat_template_id": "builtin.chat",
            "retriever_ids": [],
            "model": self.model_name,
        }

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.post(url, headers=headers, json=body, verify=False)
        response.raise_for_status()

        chat_data = response.json()
        self.chatroom_id = chat_data["id"]
        return self.chatroom_id

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:

        # 最新のユーザーメッセージだけを取り出す
        user_text = self._extract_latest_user_message(messages)

        # システムプロンプトとユーザーメッセージを結合
        prompt_text = self._build_input_text(user_text)

        # チャットルームIDを確保
        chat_id = self._ensure_chatroom()

        # アクセストークン取得
        token = self._get_access_token()
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        # ユーザーメッセージを送信
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages"
        body = {"role": "user", "content": prompt_text}
        response = requests.post(url, headers=headers, json=body, verify=False)
        response.raise_for_status()

        # AI応答を取得
        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages/createNextAiMessage"
        response = requests.post(url, headers=headers, verify=False)
        response.raise_for_status()

        ai_response = response.json()
        ai_message_content = ai_response.get("content", "")

        # ChatResultを作成して返す
        message = AIMessage(content=ai_message_content)
        generation = ChatGeneration(message=message)

        return ChatResult(generations=[generation])

    @staticmethod
    def _extract_latest_user_message(messages: List[BaseMessage]) -> str:
        last_human: Optional[HumanMessage] = None
        for m in messages:
            if isinstance(m, HumanMessage):
                last_human = m
        if last_human is not None:
            return last_human.content
        # HumanMessageが見つからない場合は最後のメッセージを返す
        return messages[-1].content if messages else ""

    def _build_input_text(self, user_text: str) -> str:
        if not self.system_prompt:
            return user_text
        return f"{self.system_prompt}\n\nUser: {user_text}"
