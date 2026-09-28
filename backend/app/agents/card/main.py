from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from app.agents.card.card_agent import build_card_graph
from shared.context import SecurityContext
from shared.internal_token import verify_internal_token
from shared.config import settings


# =========================================================
# PERSISTENT CHECKPOINTER
# =========================================================

checkpointer = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global checkpointer

    async with AsyncPostgresSaver.from_conn_string(
        settings.LANGGRAPH_CHECKPOINT_DATABASE_URL
    ) as saver:

        await saver.setup()

        checkpointer = saver

        print(
            "[CHECKPOINT] PostgreSQL checkpointer initialized"
        )

        yield

        print(
            "[CHECKPOINT] PostgreSQL checkpointer shutting down"
        )

        checkpointer = None


app = FastAPI(
    title="Card Agent",
    lifespan=lifespan,
)


# =========================================================
# REQUEST MODELS
# =========================================================

class CardAgentRequest(BaseModel):
    request: str
    conversation_id: int


class CardApprovalRequest(BaseModel):
    conversation_id: int
    approved: bool


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "card-agent",
    }


# =========================================================
# INVOKE CARD AGENT
# =========================================================

@app.post("/invoke")
async def invoke_card_agent(
    payload: CardAgentRequest,
    authorization: str | None = Header(default=None),
):

    # ==================================================
    # AUTHENTICATION
    # ==================================================

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

    # ==================================================
    # SECURITY CONTEXT
    # ==================================================

    context = SecurityContext(
        user_id=int(token_payload["sub"]),
        role=token_payload["role"],
        conversation_id=payload.conversation_id,
    )

    # ==================================================
    # CHECKPOINTER
    # ==================================================

    if checkpointer is None:
        raise HTTPException(
            status_code=503,
            detail="Checkpoint system is not ready",
        )

    # ==================================================
    # BUILD GRAPH
    # ==================================================

    graph = await build_card_graph(
        context=context,
        conversation_id=payload.conversation_id,
        checkpointer=checkpointer,
    )

    # ==================================================
    # INVOKE
    # ==================================================

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
            "intent": None,
            "selected_worker": None,
            "tool_calls": [],
            "tool_results": [],
            "requires_approval": False,
            "approval_status": None,
            "retrieved_documents": [],
        },
        config={
            "configurable": {
                "thread_id": (
                    f"card-{payload.conversation_id}"
                ),
            }
        },
    )

    # ==================================================
    # HANDLE INTERRUPT
    # ==================================================

    interrupts = result.get("__interrupt__")

    if interrupts:

        approval_data = interrupts[0].value

        return {
            "status": "APPROVAL_REQUIRED",
            "conversation_id": (
                payload.conversation_id
            ),
            **approval_data,
        }

    # ==================================================
    # NORMAL RESPONSE
    # ==================================================

    return {
        "status": "COMPLETED",
        "conversation_id": (
            payload.conversation_id
        ),
        "response": (
            result["messages"][-1].content
        ),
    }


# =========================================================
# RESUME CARD APPROVAL
# =========================================================

@app.post("/resume")
async def resume_card_approval(
    payload: CardApprovalRequest,
    authorization: str | None = Header(default=None),
):

    # ==================================================
    # AUTHENTICATION
    # ==================================================

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

    # ==================================================
    # SECURITY CONTEXT
    # ==================================================

    context = SecurityContext(
        user_id=int(token_payload["sub"]),
        role=token_payload["role"],
        conversation_id=payload.conversation_id,
    )

    # ==================================================
    # CHECKPOINTER
    # ==================================================

    if checkpointer is None:
        raise HTTPException(
            status_code=503,
            detail="Checkpoint system is not ready",
        )

    print(
        "[HITL DEBUG] Card Agent resuming "
        f"user_id={context.user_id}, "
        f"conversation_id={payload.conversation_id}, "
        f"approved={payload.approved}"
    )

    # ==================================================
    # BUILD GRAPH WITH SAME CHECKPOINTER
    # ==================================================

    graph = await build_card_graph(
        context=context,
        conversation_id=payload.conversation_id,
        checkpointer=checkpointer,
    )

    # ==================================================
    # SAME THREAD ID
    # ==================================================

    config = {
        "configurable": {
            "thread_id": (
                f"card-{payload.conversation_id}"
            ),
        }
    }

    # ==================================================
    # CHECK SAVED STATE
    # ==================================================

    saved_state = await graph.aget_state(config)

    print(
        "[HITL DEBUG] Saved state next =",
        saved_state.next,
    )

    print(
        "[HITL DEBUG] Saved state values keys =",
        list(saved_state.values.keys()),
    )

    print(
        "[HITL DEBUG] Saved state tasks =",
        saved_state.tasks,
    )

    # ==================================================
    # RESUME PAUSED GRAPH
    # ==================================================

    result = await graph.ainvoke(
        Command(
            resume={
                "approved": payload.approved,
            }
        ),
        config=config,
    )

    # ==================================================
    # HANDLE ANOTHER INTERRUPT
    # ==================================================

    interrupts = result.get("__interrupt__")

    if interrupts:

        approval_data = interrupts[0].value

        return {
            "status": "APPROVAL_REQUIRED",
            "conversation_id": (
                payload.conversation_id
            ),
            **approval_data,
        }

    # ==================================================
    # COMPLETED
    # ==================================================

    return {
        "status": "COMPLETED",
        "conversation_id": (
            payload.conversation_id
        ),
        "response": (
            result["messages"][-1].content
        ),
    }