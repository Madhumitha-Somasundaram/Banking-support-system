from datetime import datetime, timedelta, timezone

import jwt

from shared.config import settings


INTERNAL_TOKEN_EXPIRE_MINUTES = 5


def create_internal_token(
    user_id: int,
    role: str,
    conversation_id: int | None = None,
) -> str:
    """
    Create a short-lived token for trusted service-to-service calls.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "internal_service",
        "conversation_id": conversation_id,
        "iat": now,
        "exp": now + timedelta(
            minutes=INTERNAL_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_internal_token(token: str) -> dict:
    """
    Verify and decode an internal service token.
    """

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    if payload.get("type") != "internal_service":
        raise ValueError("Invalid internal token")

    if not payload.get("sub"):
        raise ValueError("Internal token missing user identity")

    if not payload.get("role"):
        raise ValueError("Internal token missing role")

    return payload