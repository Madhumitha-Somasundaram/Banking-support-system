import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class AgentJob(Base):
    __tablename__ = "agent_jobs"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    conversation_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    job_type = Column(
        String(50),
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
        default="QUEUED",
        index=True,
    )

    request = Column(
        Text,
        nullable=True,
    )

    approved = Column(
        Integer,
        nullable=True,
    )

    approval_data = Column(
        JSON,
        nullable=True,
    )

    result_message_id = Column(
        Integer,
        nullable=True,
    )

    error = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )