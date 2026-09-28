from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langgraph.types import Command

from app.db.database import get_db
from app.repository.critical_task_repository import (
    CriticalTaskRepository,
)
from shared.authorization import (
    get_authorization_service,
    PermissionDenied,
)
from shared.context import SecurityContext
from app.agents.workers.card_agent import build_card_graph
from shared.dependencies import get_current_user


router = APIRouter(
    prefix="/api/critical-tasks",
    tags=["Critical Tasks"],
)

task_repository = CriticalTaskRepository()
authorization_service = get_authorization_service()

@router.post("/{task_id}/approve")
async def approve_critical_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = task_repository.get_by_id(
        db=db,
        task_id=task_id,
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Approval task not found.",
        )

    # ---------------------------------------------
    # Ownership
    # ---------------------------------------------

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this task.",
        )

    # ---------------------------------------------
    # Must still be pending
    # ---------------------------------------------

    if task.status.value != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Task is already {task.status.value}.",
        )

    # ---------------------------------------------
    # Expiration
    # ---------------------------------------------

    if task.is_expired():
        task.status = "expired"
        db.commit()

        raise HTTPException(
            status_code=409,
            detail="Approval task has expired.",
        )

    # ---------------------------------------------
    # Role authorization
    # ---------------------------------------------

    if not task.can_be_approved_by(
        current_user.role
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to approve this task.",
        )

    # ---------------------------------------------
    # Approve
    # ---------------------------------------------

    approved_task = task_repository.approve(
        db=db,
        task_id=task_id,
        approved_by_user_id=current_user.id,
        approval_reason="Approved by user.",
    )

    if not approved_task:
        raise HTTPException(
            status_code=404,
            detail="Approval task not found.",
        )

    conversation_id = approved_task.task_data.get(
        "conversation_id"
    )

    if not conversation_id:
        raise HTTPException(
            status_code=500,
            detail="Approval task is missing conversation context.",
        )

    # ---------------------------------------------
    # Rebuild the SAME Card Agent graph
    # ---------------------------------------------

    context = SecurityContext(
        user_id=current_user.id,
        role=current_user.role,
        conversation_id=conversation_id,
    )

    card_graph = await build_card_graph(
        
        context=context,
    )

    # ---------------------------------------------
    # Resume the interrupted Card Agent
    # ---------------------------------------------

    result = await card_graph.ainvoke(
        Command(
            resume={
                "approved": True,
            }
        ),
        config={
            "configurable": {
                "thread_id": f"card-{conversation_id}",
            }
        },
    )

    return {
        "status": "EXECUTED",
        "task_id": task_id,
        "result": result["messages"][-1].content,
    }


@router.post("/{task_id}/reject")
async def reject_critical_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = task_repository.get_by_id(
        db=db,
        task_id=task_id,
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Approval task not found.",
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this task.",
        )

    if task.status.value != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Task is already {task.status.value}.",
        )

    if task.is_expired():
        task.status = "expired"
        db.commit()

        raise HTTPException(
            status_code=409,
            detail="Approval task has expired.",
        )

    if not task.can_be_approved_by(
        current_user.role
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to reject this task.",
        )

    rejected_task = task_repository.reject(
        db=db,
        task_id=task_id,
        rejection_reason="Rejected by user.",
    )

    return {
        "status": "REJECTED",
        "task_id": task_id,
        "message": "The card action was rejected.",
    }