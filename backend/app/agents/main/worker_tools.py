import json

from langchain_core.tools import tool

from shared.context import SecurityContext
from shared.config import settings

from app.agents.main.worker_client import WorkerAgentClient


def create_worker_tools(
    context: SecurityContext,
    conversation_id: int,
):

    client = WorkerAgentClient(
        context=context,
    )

    @tool
    async def account_support(
        request: str,
    ) -> str:
        """
        Handle account-related questions.
        """
        result = await client.call(
            url=settings.ACCOUNT_AGENT_URL,
            request=request,
            conversation_id=conversation_id,
        )

        return result["response"]

    @tool
    async def transaction_support(
        request: str,
    ) -> str:
        """
        Handle transaction-related questions.
        """
        result = await client.call(
            url=settings.TRANSACTION_AGENT_URL,
            request=request,
            conversation_id=conversation_id,
        )

        return result["response"]

    @tool
    async def card_support(
        request: str,
    ) -> str:
        """
        Handle card-related questions.
        """
        result = await client.call(
            url=settings.CARD_AGENT_URL,
            request=request,
            conversation_id=conversation_id,
        )

        if result.get("status") == "APPROVAL_REQUIRED":
            return json.dumps(result)

        return result["response"]

    @tool
    async def rag_support(
        request: str,
    ) -> str:
        """
        Handle banking policy and knowledge-base questions.
        """
        result = await client.call(
            url=settings.RAG_AGENT_URL,
            request=request,
            conversation_id=conversation_id,
        )

        return result["response"]

    return [
        account_support,
        transaction_support,
        card_support,
        rag_support,
    ]