"""Repository for Critical Task CRUD operations."""

from sqlalchemy.orm import Session
from app.critical_tasks.models.critical_task import CriticalTask, TaskStatus, TaskSeverity, TaskType
from datetime import datetime, timedelta
from typing import Optional, List


class CriticalTaskRepository:
    """Manages critical task database operations."""

    def create(
        self,
        db: Session,
        task_id: str,
        task_type: TaskType,
        severity: TaskSeverity,
        user_id: int,
        requester_role: str,
        task_data: dict,
        expires_in_hours: int = 1,
    ) -> CriticalTask:
        """Create a new critical task."""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

        task = CriticalTask(
            task_id=task_id,
            task_type=task_type,
            severity=severity,
            status=TaskStatus.PENDING,
            user_id=user_id,
            requester_role=requester_role,
            task_data=task_data,
            expires_at=expires_at,
        )

        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_by_id(self, db: Session, task_id: str) -> Optional[CriticalTask]:
        """Get task by task_id (UUID)."""
        return db.query(CriticalTask).filter(CriticalTask.task_id == task_id).first()

    def get_by_db_id(self, db: Session, db_id: int) -> Optional[CriticalTask]:
        """Get task by database ID."""
        return db.query(CriticalTask).filter(CriticalTask.id == db_id).first()

    def get_pending(
        self,
        db: Session,
        user_id: Optional[int] = None,
    ) -> List[CriticalTask]:
        """Get all pending (non-expired) tasks, optionally filtered by user."""
        now = datetime.utcnow()

        query = db.query(CriticalTask).filter(
            CriticalTask.status == TaskStatus.PENDING,
            CriticalTask.expires_at > now,
        )

        if user_id:
            query = query.filter(CriticalTask.user_id == user_id)

        return query.all()

    def get_pending_for_approval(
        self,
        db: Session,
        approver_role: str,
    ) -> List[CriticalTask]:
        """Get pending tasks that can be approved by given role."""
        now = datetime.utcnow()

        tasks = db.query(CriticalTask).filter(
            CriticalTask.status == TaskStatus.PENDING,
            CriticalTask.expires_at > now,
        ).all()

        # Filter by role permissions
        approvable = [t for t in tasks if t.can_be_approved_by(approver_role)]
        return approvable

    def approve(
        self,
        db: Session,
        task_id: str,
        approved_by_user_id: int,
        approval_reason: str = "",
    ) -> Optional[CriticalTask]:

        task = self.get_by_id(
            db,
            task_id,
        )

        if not task:
            return None

        if task.status != TaskStatus.PENDING:
            return task

        if task.is_expired():
            task.status = TaskStatus.EXPIRED
            db.commit()
            db.refresh(task)
            return task

        task.status = TaskStatus.APPROVED
        task.approved_by = approved_by_user_id
        task.approved_at = datetime.utcnow()
        task.approval_reason = approval_reason

        db.commit()
        db.refresh(task)

        return task
    def reject(
        self,
        db: Session,
        task_id: str,
        rejection_reason: str = "",
    ) -> Optional[CriticalTask]:
        """Reject a critical task."""
        task = self.get_by_id(db, task_id)
        if not task:
            return None

        task.status = TaskStatus.REJECTED
        task.rejection_reason = rejection_reason

        db.commit()
        db.refresh(task)
        return task

    def mark_executed(self, db: Session, task_id: str) -> Optional[CriticalTask]:
        """Mark a task as executed."""
        task = self.get_by_id(db, task_id)
        if not task:
            return None

        task.status = TaskStatus.EXECUTED
        task.executed_at = datetime.utcnow()

        db.commit()
        db.refresh(task)
        return task

    def cleanup_expired(self, db: Session) -> int:
        """Mark all expired pending tasks as expired and return count."""
        now = datetime.utcnow()

        expired_count = db.query(CriticalTask).filter(
            CriticalTask.status == TaskStatus.PENDING,
            CriticalTask.expires_at <= now,
        ).update({CriticalTask.status: TaskStatus.EXPIRED})

        db.commit()
        return expired_count


# Task severity and approval requirements by amount
TASK_REQUIREMENTS = {
   
    TaskType.FREEZE_ACCOUNT: {
        "default_severity": TaskSeverity.HIGH,
    },
    TaskType.CLOSE_ACCOUNT: {
        "default_severity": TaskSeverity.CRITICAL,
    },
    TaskType.FREEZE_CARD: {
        "default_severity": TaskSeverity.MEDIUM,
    },
    TaskType.UNFREEZE_CARD: {
        "default_severity": TaskSeverity.MEDIUM,
    },
}

def get_task_severity(
    task_type: TaskType,
    amount: Optional[float] = None,
) -> TaskSeverity:
    """Determine task severity based on type and amount."""
    requirements = TASK_REQUIREMENTS.get(task_type)

    if not requirements:
        return TaskSeverity.LOW

    # Non-monetary tasks with default severity
    if "default_severity" in requirements:
        return requirements["default_severity"]

    # Monetary tasks: check thresholds
    if amount is None:
        return TaskSeverity.MEDIUM

    if amount <= requirements.get("threshold_low", 0):
        return TaskSeverity.LOW

    if amount <= requirements.get("threshold_medium", float("inf")):
        return TaskSeverity.MEDIUM

    return TaskSeverity.HIGH
