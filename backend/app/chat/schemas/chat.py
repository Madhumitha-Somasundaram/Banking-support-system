from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):

    content: str


class MessageResponse(BaseModel):

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):

    type: str
    action: str
    card_id: int
    last4: str
    message: str
    description: str | None = None


class ChatResponse(BaseModel):

    messages: list[MessageResponse]

    approval: ApprovalResponse | None = None

    job_id: str | None = None

    status: str | None = None


class JobStatusResponse(BaseModel):

    job_id: str

    conversation_id: int

    status: str

    message: MessageResponse | None = None

    approval: ApprovalResponse | None = None

    error: str | None = None


class CardApprovalRequest(BaseModel):

    approved: bool