"""
Card Service REST API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.card.db.database import get_db
from services.card.service.card_service import CardService


router = APIRouter(
    prefix="/cards",
    tags=["cards"],
)

card_service = CardService()


# =========================================================
# READ
# =========================================================


@router.get("/")
def list_cards(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    account_id: int | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    List cards for a user.
    """

    return card_service.list_cards(
        db=db,
        user_id=user_id,
        account_id=account_id,
        status=status,
    )


@router.get("/details")
def get_card_details(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    card_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_id: int | None = Query(None),
    card_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Resolve a card and return its details.
    """

    return card_service.get_details(
        db=db,
        user_id=user_id,
        card_number=card_number,
        last4=last4,
        account_id=account_id,
        card_type=card_type,
    )


@router.get("/status")
def get_card_status(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    card_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_id: int | None = Query(None),
    card_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get the status of a card.
    """

    return card_service.get_status(
        db=db,
        user_id=user_id,
        card_number=card_number,
        last4=last4,
        account_id=account_id,
        card_type=card_type,
    )


@router.get("/limits")
def get_card_limits(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    card_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_id: int | None = Query(None),
    card_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get purchase and ATM limits.
    """

    return card_service.get_limits(
        db=db,
        user_id=user_id,
        card_number=card_number,
        last4=last4,
        account_id=account_id,
        card_type=card_type,
    )


# =========================================================
# WRITE
# =========================================================


@router.post("/freeze")
def freeze_card(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    card_number: str | None = Query(None),
    last4: str | None = Query(None),
    execute: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Freeze a card.

    execute=False:
        Returns APPROVAL_REQUIRED.

    execute=True:
        Performs the actual state change.
    """

    return card_service.freeze_card(
        db=db,
        user_id=user_id,
        card_number=card_number,
        last4=last4,
        execute=execute,
    )


@router.post("/unfreeze")
def unfreeze_card(
    user_id: int = Query(
        ...,
        description="User ID",
    ),
    card_number: str | None = Query(None),
    last4: str | None = Query(None),
    execute: bool = Query(False),
    db: Session = Depends(get_db),
):
    """
    Unfreeze a card.

    execute=False:
        Returns APPROVAL_REQUIRED.

    execute=True:
        Performs the actual state change.
    """

    return card_service.unfreeze_card(
        db=db,
        user_id=user_id,
        card_number=card_number,
        last4=last4,
        execute=execute,
    )