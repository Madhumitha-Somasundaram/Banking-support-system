"""
Critical Task Model - Database-backed storage for approval workflows.

Certain banking operations require human approval before execution:
  - Transfer Money: Amount > threshold
  - Freeze Account: Requires admin approval
  - Close Account: Requires admin approval
  - Withdraw Large Amount: Amount > threshold
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from enum import Enum
from datetime import datetime


class TaskSeverity(str, Enum):
    """Severity level of critical tasks."""
    LOW = "low"              # View-only, auto-approved
    MEDIUM = "medium"        # Needs user confirmation
    HIGH = "high"            # Needs admin approval
    CRITICAL = "critical"    # Multi-factor approval


class TaskStatus(str, Enum):
    """Status of critical task."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class TaskType(str, Enum):
    """Types of critical tasks."""


    FREEZE_ACCOUNT = "freeze_account"
    FREEZE_CARD = "freeze_card"
    UNFREEZE_CARD = "unfreeze_card"

    CLOSE_ACCOUNT = "close_account"



class CriticalTask(Base):
    """
    Critical task requiring approval before execution.

    Stores:
      - Task metadata (type, severity, status)
      - Task data (amount, accounts involved, etc.)
      - Approval chain (who requested, who approved)
      - Timeline (created, expires, executed)
    """

    __tablename__ = "critical_tasks"

    # Identifiers
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, nullable=False, index=True)

    # Task classification
    task_type = Column(SQLEnum(TaskType), nullable=False)
    severity = Column(SQLEnum(TaskSeverity), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)

    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requester_role = Column(String(50), nullable=False)  # Role at request time

    # Task payload (flexible JSON for different task types)
    task_data = Column(JSON, nullable=False)

    # Timeline
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Approval chain
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_reason = Column(String(500), nullable=True)
    rejection_reason = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="created_tasks")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_tasks")

    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        return datetime.utcnow() > self.expires_at

    def is_approved(self) -> bool:
        """Check if task is approved and not expired."""
        return self.status == TaskStatus.APPROVED and not self.is_expired()

    def is_pending(self) -> bool:
        """Check if task is still pending approval."""
        return self.status == TaskStatus.PENDING and not self.is_expired()

    def can_be_approved_by(self, user_role: str) -> bool:
        """
        Check if user role can approve this task.

        Approval rules:
          - CRITICAL: Requires admin (+ customer for MFA scenarios)
          - HIGH: Requires admin
          - MEDIUM: Requires user (self) or admin
          - LOW: Auto-approved, no user action needed
        """
        if self.severity == TaskSeverity.LOW:
            return True

        if self.severity == TaskSeverity.MEDIUM:
            return user_role in ("CUSTOMER", "ADMIN")

        if self.severity == TaskSeverity.HIGH:
            return user_role == "ADMIN"

        if self.severity == TaskSeverity.CRITICAL:
            return user_role == "ADMIN"

        return False
