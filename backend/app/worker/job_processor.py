from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.main.worker_client import WorkerAgentClient
from app.chat.models.jobs import AgentJob
from app.chat.repository.job_repository import JobRepository
from app.chat.repository.message_repository import MessageRepository

from app.chat.models.conversations import Conversation

from app.worker.main_agent import WorkerMainAgent

from shared.context import SecurityContext
from shared.internal_token import create_internal_token
from shared.config import settings


class JobProcessor:

    def __init__(self):

        self.job_repository = JobRepository()

        self.message_repository = MessageRepository()

        self.main_agent = WorkerMainAgent()

    def get_job(
        self,
        db: Session,
        job_id: str,
    ):

        return self.job_repository.get_by_id(
            db,
            job_id,
        )

    async def process(
        self,
        db: Session,
        payload: dict,
    ):

        job_id = payload["job_id"]

        job = self.get_job(
            db,
            job_id,
        )

        if job is None:
            raise ValueError(
                f"Job {job_id} does not exist"
            )

        # Idempotency:
        # If another worker already completed this job,
        # do not execute the banking operation again.
        if job.status in {
            "COMPLETED",
            "APPROVAL_REQUIRED"
        }:
            return

        self.job_repository.mark_processing(
            db,
            job_id,
        )

        try:

            if job.job_type == "MESSAGE":

                await self.process_message(
                    db=db,
                    job=job,
                    payload=payload,
                )

            elif job.job_type == "CARD_APPROVAL":

                await self.process_card_approval(
                    db=db,
                    job=job,
                    payload=payload,
                )

            else:

                raise ValueError(
                    f"Unknown job type: {job.job_type}"
                )

        except Exception as exc:

            print(
                f"[WORKER ERROR] "
                f"job_id={job_id} "
                f"error={exc}"
            )

            self.job_repository.mark_failed(
                db,
                job_id,
                "We could not process your request. "
                "Please try again.",
            )

            raise

    async def process_message(
        self,
        db: Session,
        job: AgentJob,
        payload: dict,
    ):

        messages = (
            self.message_repository
            .get_by_conversation(
                db,
                job.conversation_id,
            )
        )

        agent_messages = []

        from langchain_core.messages import (
            HumanMessage,
            AIMessage,
        )

        for message in messages:

            if message.role == "USER":

                agent_messages.append(
                    HumanMessage(
                        content=message.content
                    )
                )

            elif message.role == "ASSISTANT":

                agent_messages.append(
                    AIMessage(
                        content=message.content
                    )
                )

        result = await self.main_agent.run(
            messages=agent_messages,
            user_id=job.user_id,
            role=payload["role"],
            conversation_id=job.conversation_id,
        )

        if result["type"] == "approval_required":

            self.job_repository.mark_approval_required(
                db=db,
                job_id=job.id,
                approval_data=result["approval"],
            )

            return

        assistant_message = (
            self.message_repository.create(
                db,
                job.conversation_id,
                "ASSISTANT",
                result["content"],
            )
        )

        self.job_repository.mark_completed(
            db=db,
            job_id=job.id,
            result_message_id=assistant_message.id,
        )

    async def process_card_approval(
        self,
        db: Session,
        job: AgentJob,
        payload: dict,
    ):

        internal_token = create_internal_token(
            user_id=job.user_id,
            role=payload["role"],
            conversation_id=job.conversation_id,
        )

        context = SecurityContext(
            user_id=job.user_id,
            role=payload["role"],
            conversation_id=job.conversation_id,
            internal_token=internal_token,
        )

        client = WorkerAgentClient(
            context=context,
        )

        resume_url = (
            settings.CARD_AGENT_URL
            .replace(
                "/invoke",
                "/resume",
            )
        )

        result = await client.resume_card(
            url=resume_url,
            conversation_id=job.conversation_id,
            approved=bool(job.approved),
        )

        if result.get(
            "status"
        ) == "APPROVAL_REQUIRED":

            self.job_repository.mark_approval_required(
                db=db,
                job_id=job.id,
                approval_data=result,
            )

            return

        response = result.get(
            "response",
            "Your request has been processed.",
        )

        assistant_message = (
            self.message_repository.create(
                db,
                job.conversation_id,
                "ASSISTANT",
                response,
            )
        )

        self.job_repository.mark_completed(
            db=db,
            job_id=job.id,
            result_message_id=assistant_message.id,
        )