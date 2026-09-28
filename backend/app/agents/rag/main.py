
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.agents.rag.rag_agent import RAGAgent
from shared.context import SecurityContext
from shared.internal_token import verify_internal_token


app = FastAPI(
    title="RAG Agent",
    version="1.0.0",
)


class RAGAgentRequest(BaseModel):
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
    except Exception as e:
        print(f"[RAG AUTH DEBUG] {type(e).__name__}: {e}")

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
        "service": "rag-agent",
    }


@app.post("/invoke")
async def invoke_rag_agent(
    payload: RAGAgentRequest,
    authorization: str | None = Header(default=None),
):
    """
    Main Agent calls this endpoint to execute
    the RAG Agent.
    """
    print(f"[RAG DEBUG] Authorization header present: {authorization is not None}")
    context = get_security_context(
        authorization=authorization,
        conversation_id=payload.conversation_id,
    )
    print(f"[RAG DEBUG] {context}")
    agent = RAGAgent(
        context=context,
    )

    result = await agent.run(
        request=payload.request,
    )

    return {
        "status": "COMPLETED",
        "conversation_id": payload.conversation_id,
        "response": result,
    }

