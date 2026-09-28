from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.chat.service.chat_service import ChatService

from app.chat.schemas.chat import (
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    CardApprovalRequest,
    ChatResponse,
    ApprovalResponse,
    JobStatusResponse,
)

from app.user.dependencies import get_current_user
from app.db.database import get_db


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


chat_service = ChatService()


@router.post(
    "/conversations",
    response_model=ConversationResponse,
)
def create_conversation(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.create_conversation(
        db,
        current_user.id,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def get_user_conversations(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.get_user_conversations(
        db,
        current_user.id,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.get_conversation(
        db,
        conversation_id,
        current_user.id,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatResponse,
    status_code=202,
)
async def send_message(
    conversation_id: int,
    message: MessageCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    result = await chat_service.add_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role=current_user.role,
        content=message.content,
    )

    messages = [
        result["user_message"]
    ]

    return ChatResponse(
        messages=messages,
        approval=None,
        job_id=result["job_id"],
        status=result["status"],
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.get_messages(
        db,
        conversation_id,
        current_user.id,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_job(
    job_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return chat_service.get_job(
        db,
        job_id,
        current_user.id,
    )


@router.post(
    "/conversations/{conversation_id}/card-approval",
    response_model=ChatResponse,
    status_code=202,
)
async def handle_card_approval(
    conversation_id: int,
    request: CardApprovalRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):

    result = await chat_service.resume_card_approval(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role=current_user.role,
        approved=request.approved,
    )

    return ChatResponse(
        messages=[],
        approval=None,
        job_id=result["job_id"],
        status=result["status"],
    )