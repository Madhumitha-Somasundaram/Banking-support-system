
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.agents.transaction.transaction_agent import build_transaction_graph
from shared.context import SecurityContext
from shared.internal_token import verify_internal_token


app = FastAPI(
    title="Transaction Agent",
    version="1.0.0",
)


class TransactionAgentRequest(BaseModel):
    request: str
    conversation_id: int


def get_security_context(
    authorization: str | None,
    conversation_id: int,
) -> SecurityContext:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = verify_internal_token(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid internal authentication",
        )

    return SecurityContext(
        user_id=int(payload["sub"]),
        role=payload["role"],
        conversation_id=conversation_id,
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "transaction-agent",
    }


@app.post("/invoke")
async def invoke_transaction_agent(
    payload: TransactionAgentRequest,
    authorization: str | None = Header(default=None),
):
    """
    Main Agent calls this endpoint to execute
    the Transaction Support Agent.
    """

    context = get_security_context(
        authorization=authorization,
        conversation_id=payload.conversation_id,
    )

    graph = await build_transaction_graph(
        context=context,
    )

    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": payload.request,
            }
        ],
        "user_id": context.user_id,
        "conversation_id": payload.conversation_id,
        "user_role": context.role,
        "intent": None,
        "selected_worker": None,
        "worker_results": [],
        "retrieved_documents": [],
        "approval": None,
        "iteration": 0,
        "final_answer": None,
    }

    result = await graph.ainvoke(
        initial_state,
    )

    messages = result.get("messages", [])

    if not messages:
        return {
            "status": "COMPLETED",
            "conversation_id": payload.conversation_id,
            "response": "I could not process the request.",
        }

    final_message = messages[-1]

    response_text = getattr(
        final_message,
        "content",
        str(final_message),
    )

    return {
        "status": "COMPLETED",
        "conversation_id": payload.conversation_id,
        "response": response_text,
    }

