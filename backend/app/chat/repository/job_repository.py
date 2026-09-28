from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.chat.models.jobs import AgentJob


class JobRepository:

    def create(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
        job_type: str,
        request: str | None = None,
        approved: bool | None = None,
    ) -> AgentJob:

        job = AgentJob(
            conversation_id=conversation_id,
            user_id=user_id,
            job_type=job_type,
            status="QUEUED",
            request=request,
            approved=(
                1 if approved is True
                else 0 if approved is False
                else None
            ),
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    def get_by_id(
        self,
        db: Session,
        job_id: str,
    ) -> AgentJob | None:

        return (
            db.query(AgentJob)
            .filter(AgentJob.id == job_id)
            .first()
        )

    def mark_processing(
        self,
        db: Session,
        job_id: str,
    ):

        job = self.get_by_id(db, job_id)

        if job is None:
            return None

        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)
        job.error = None

        db.commit()
        db.refresh(job)

        return job

    def mark_completed(
        self,
        db: Session,
        job_id: str,
        result_message_id: int | None = None,
    ):

        job = self.get_by_id(db, job_id)

        if job is None:
            return None

        job.status = "COMPLETED"
        job.result_message_id = result_message_id
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

        return job

    def mark_approval_required(
        self,
        db: Session,
        job_id: str,
        approval_data: dict,
    ):

        job = self.get_by_id(db, job_id)

        if job is None:
            return None

        job.status = "APPROVAL_REQUIRED"
        job.approval_data = approval_data

        db.commit()
        db.refresh(job)

        return job

    def mark_failed(
        self,
        db: Session,
        job_id: str,
        error: str,
    ):

        job = self.get_by_id(db, job_id)

        if job is None:
            return None

        job.status = "FAILED"
        job.error = error
        job.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(job)

        return job