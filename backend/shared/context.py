"""Security Context - Carries authentication and authorization info through agent execution."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SecurityContext:
    """
    Security context passed through agent execution.

    Immutable dataclass carrying user identity, authorization,
    conversation, and service-to-service authentication information.
    """

    user_id: int
    role: str
    email: str = ""
    name: str = ""
    conversation_id: int | None = None
    internal_token: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == "ADMIN"

    def is_support(self) -> bool:
        """Check if user is support agent."""
        return self.role == "SUPPORT_AGENT"

    def is_customer(self) -> bool:
        """Check if user is customer."""
        return self.role == "CUSTOMER"