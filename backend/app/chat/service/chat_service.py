from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.chat.repository.conversation_repository import (
    ConversationRepository,
)

from app.chat.repository.message_repository import (
    MessageRepository,
)

from app.chat.repository.job_repository import (
    JobRepository,
)

from app.agents.main.main_agent import MainAgent
from opentelemetry import trace


tracer = trace.get_tracer(
    "banking-main-backend"
)

class ChatService:

    def __init__(self):

        self.conversation_repository = (
            ConversationRepository()
        )

        self.message_repository = (
            MessageRepository()
        )

        self.job_repository = (
            JobRepository()
        )

        self.main_agent = MainAgent()

    def create_conversation(
        self,
        db: Session,
        user_id: int,
    ):

        return self.conversation_repository.create(
            db,
            user_id,
        )

    def get_user_conversations(
        self,
        db: Session,
        user_id: int,
    ):

        return self.conversation_repository.get_by_user(
            db,
            user_id,
        )

    def get_conversation(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
    ):

        conversation = (
            self.conversation_repository.get_by_id(
                db,
                conversation_id,
            )
        )

        if conversation is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.user_id != user_id:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation",
            )

        return conversation

    async def add_message(
    self,
    db: Session,
    conversation_id: int,
    user_id: int,
    role: str,
    content: str,
):

        conversation = self.get_conversation(
            db,
            conversation_id,
            user_id,
        )

        # --------------------------------------------------
        # Save user message
        # --------------------------------------------------

        user_message = (
            self.message_repository.create(
                db,
                conversation.id,
                "USER",
                content,
            )
        )

        # --------------------------------------------------
        # Create job
        # --------------------------------------------------

        job = self.job_repository.create(
            db=db,
            conversation_id=conversation.id,
            user_id=user_id,
            job_type="MESSAGE",
            request=content,
        )

        # --------------------------------------------------
        # Trace job submission
        # --------------------------------------------------

        with tracer.start_as_current_span(
            "chat.submit_agent_job"
        ) as span:

            span.set_attribute(
                "banking.job_id",
                str(job.id),
            )

            span.set_attribute(
                "banking.conversation_id",
                str(conversation.id),
            )

            span.set_attribute(
                "banking.operation",
                "submit_agent_job",
            )

            span.set_attribute(
                "banking.agent",
                "main",
            )

            try:

                await self.main_agent.submit(
                    job_id=job.id,
                    request=content,
                    user_id=user_id,
                    role=role,
                    conversation_id=conversation.id,
                )

                span.set_attribute(
                    "banking.status",
                    "queued",
                )

            except Exception as exc:

                span.set_attribute(
                    "banking.status",
                    "failed",
                )

                span.record_exception(exc)

                self.job_repository.mark_failed(
                    db,
                    job.id,
                    "We could not queue your request.",
                )

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Unable to queue your request. "
                        "Please try again."
                    ),
                )

        return {
            "user_message": user_message,
            "assistant_message": None,
            "approval": None,
            "job_id": job.id,
            "status": "QUEUED",
        }
    def get_messages(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
    ):

        self.get_conversation(
            db,
            conversation_id,
            user_id,
        )

        return (
            self.message_repository
            .get_by_conversation(
                db,
                conversation_id,
            )
        )

    async def resume_card_approval(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
        role: str,
        approved: bool,
    ):

        conversation = self.get_conversation(
            db,
            conversation_id,
            user_id,
        )

        job = self.job_repository.create(
            db=db,
            conversation_id=conversation.id,
            user_id=user_id,
            job_type="CARD_APPROVAL",
            approved=approved,
        )

        try:

            await self.main_agent.submit_card_approval(
                job_id=job.id,
                user_id=user_id,
                role=role,
                conversation_id=conversation.id,
                approved=approved,
            )

        except Exception:

            self.job_repository.mark_failed(
                db,
                job.id,
                "We could not queue your approval.",
            )

            raise HTTPException(
                status_code=503,
                detail="Unable to process approval. Please try again.",
            )

        return {
            "assistant_message": None,
            "approval": None,
            "job_id": job.id,
            "status": "QUEUED",
        }

    def get_job(
        self,
        db: Session,
        job_id: str,
        user_id: int,
    ):

        job = self.job_repository.get_by_id(
            db,
            job_id,
        )

        if job is None:

            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        if job.user_id != user_id:

            raise HTTPException(
                status_code=403,
                detail="You do not have access to this job",
            )

        message = None

        if job.result_message_id:

            message = (
                self.message_repository
                .get_by_id(
                    db,
                    job.result_message_id,
                )
            )

        return {
            "job_id": job.id,
            "conversation_id": job.conversation_id,
            "status": job.status,
            "message": message,
            "approval": job.approval_data,
            "error": job.error,
        }