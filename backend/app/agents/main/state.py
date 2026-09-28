from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    user_id: int

    conversation_id: int

    user_role: str

    intent: str | None

    selected_worker: str | None

    worker_results: list

    retrieved_documents: list

    requires_approval: bool

    approval_status: str | None

    iteration: int

    max_iterations: int

    final_answer: str | None