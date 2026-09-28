
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.agents.account.account_agent import build_account_graph
from shared.context import SecurityContext
from shared.internal_token import verify_internal_token


app = FastAPI(
    title="Account Agent",
)


class AccountAgentRequest(BaseModel):
    request: str
    user_id: int
    role: str
    conversation_id: int

@app.get("/health")
async def health():
    return {"status": "ok", "service": "account-agent"}

@app.post("/invoke")
async def invoke_account_agent(
    payload: AccountAgentRequest,
    authorization: str | None = Header(default=None),
):
    # --------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------

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

    token = authorization.removeprefix(
        "Bearer "
    ).strip()

    try:
        token_payload = verify_internal_token(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid internal authentication",
        )

    # --------------------------------------------------
    # SECURITY CONTEXT
    # --------------------------------------------------

    context = SecurityContext(
        user_id=int(token_payload["sub"]),
        role=token_payload["role"],
        conversation_id=payload.conversation_id,
    )

    # --------------------------------------------------
    # BUILD ACCOUNT AGENT
    # --------------------------------------------------

    graph = await build_account_graph(
        context=context,
    )

    # --------------------------------------------------
    # RUN AGENT
    # --------------------------------------------------

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": payload.request,
                }
            ],
            "user_id": context.user_id,
            "conversation_id": payload.conversation_id,
            "user_role": context.role,
        }
    )

    return {
        "response": result["messages"][-1].content,
    }

