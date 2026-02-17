from TakaneLLMWrapperSimple import TakaneChatModelSimple

from typing import TypedDict, Dict
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from IPython.display import display

import os
from dotenv import load_dotenv

load_dotenv()


llm = TakaneChatModelSimple(
    tenant_name=os.getenv("TENANT_NAME"),
    client_id=os.getenv("CLIENT_ID"),
    model_name="cohere.command-r-plus-fujitsu",
    system_prompt="",
    max_tokens=1024,
    temperature=0.5,
    top_p=1.0,
)


class PersonInfo(BaseModel):
    name: str
    age: int


class TestState(TypedDict):
    user_query: str
    person: PersonInfo


def node_chatbot(state: TestState) -> Dict:
    response = llm.invoke(state["user_query"], response_format=PersonInfo)
    person = PersonInfo.model_validate_json(response.content)
    return {"person": person}


if __name__ == "__main__":
    graph = StateGraph(TestState)
    graph.add_node("chatbot", node_chatbot)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)

    workflow = graph.compile()

    display(workflow.get_graph().draw_ascii())

    final_state = workflow.invoke({"user_query": "太郎は35歳のエンジニアです。"})

    print(final_state)
