"""
Enhanced Authorization Service with RBAC.

Three-level authorization:
  1. Role-Based Access Control (RBAC) - can user's role do this?
  2. Resource Ownership - does user own the resource?
  3. Critical Task Approval - does action require approval?
"""

from shared.policies import ROLE_CAPABILITIES
from shared.context import SecurityContext
from app.critical_tasks.models.critical_task import TaskType, TaskSeverity
from app.critical_tasks.repository.critical_task_repository import (
    CriticalTaskRepository,
    get_task_severity,
)
from sqlalchemy.orm import Session
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PermissionDenied(Exception):
    """Raised when user lacks permission."""
    pass


class ResourceNotOwned(Exception):
    """Raised when user doesn't own resource."""
    pass


class CriticalTaskRequired(Exception):
    """Raised when critical task approval is needed."""

    def __init__(self, task_id: str, severity: str, message: str = ""):
        self.task_id = task_id
        self.severity = severity
        super().__init__(message)


class AuthorizationService:
    """
    RBAC Authorization Service.

    Implements three-level authorization:
      1. Role capabilities
      2. Resource ownership
      3. Critical task approval
    """

    def __init__(self):
        self.task_repo = CriticalTaskRepository()

    def authorize(
        self,
        context: SecurityContext,
        capability: str,
        resource_owner_id: Optional[int] = None,
    ) -> dict:
        """
        Check if user can perform capability.

        Args:
            context: Security context with user_id and role
            capability: Capability name to check
            resource_owner_id: User ID who owns resource (for ownership check)

        Returns:
            {"allowed": True, "requires_approval": bool}

        Raises:
            PermissionDenied: User role lacks this capability
            ResourceNotOwned: User doesn't own this resource
        """
        # Level 1: RBAC - Check role capabilities
        allowed_capabilities = ROLE_CAPABILITIES.get(context.role, set())

        if capability not in allowed_capabilities:
            logger.warning(
                f"Authorization failed: user {context.user_id} "
                f"(role={context.role}) lacks capability '{capability}'"
            )
            raise PermissionDenied(
        f"User is not authorized for capability: {capability}"
    )

        # Level 2: Resource Ownership - Check if user owns resource
        if resource_owner_id is not None:
            if resource_owner_id != context.user_id and context.role != "ADMIN":
                logger.warning(
                    f"Authorization failed: user {context.user_id} "
                    f"does not own resource {resource_owner_id}"
                )
                raise ResourceNotOwned(
    "User does not own this resource"
)

        return {
            "allowed": True,
            "requires_approval": False,
        }

    def check_critical_task(
        self,
        db: Session,
        context: SecurityContext,
        task_type: TaskType,
        amount: Optional[float] = None,
    ) -> Tuple[TaskSeverity, bool]:
        """
        Check if task requires approval.

        Args:
            db: Database session
            context: Security context
            task_type: Type of task being performed
            amount: Amount (for monetary tasks)

        Returns:
            (severity, requires_approval) tuple

        Example:
            severity, requires_approval = service.check_critical_task(
                db,
                context,
                TaskType.TRANSFER_MONEY,
                amount=10000,
            )

            if requires_approval:
                # Create approval task
                task = create_approval_task(db, context, task_data)
                raise CriticalTaskRequired(task.task_id, severity)
        """
        severity = get_task_severity(task_type, amount)

        # LOW severity doesn't require approval
        if severity == TaskSeverity.LOW:
            return severity, False

        # MEDIUM/HIGH/CRITICAL require approval
        return severity, True

    def verify_resource_access(
        self,
        context: SecurityContext,
        resource_owner_id: int,
        resource_type: str,
    ) -> None:
        """
        Verify user can access a resource.

        Args:
            context: Security context
            resource_owner_id: Owner of the resource
            resource_type: Type of resource (for logging)

        Raises:
            ResourceNotOwned: If user can't access resource
        """
        if context.role == "ADMIN":
            # Admins can access any resource
            return

        if resource_owner_id != context.user_id:
            logger.warning(
                f"Access denied: user {context.user_id} "
                f"tried to access {resource_type} owned by {resource_owner_id}"
            )
            raise ResourceNotOwned(
    f"You do not have access to this {resource_type}"
)


# Global service instance
_auth_service = None


def get_authorization_service() -> AuthorizationService:
    """Get or create singleton authorization service."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthorizationService()
    return _auth_service