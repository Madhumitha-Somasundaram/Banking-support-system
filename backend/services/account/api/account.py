"""Account Service REST API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.account.db.database import get_db
from services.account.service.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])

account_service = AccountService()


@router.get("/")
def list_accounts(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """
    List all accounts for a user.

    Args:
        user_id: User ID (required) - from authenticated context
        db: Database session

    Returns:
        List of accounts
    """
    return account_service.list_accounts(db=db, user_id=user_id)


@router.get("/balance")
def get_balance(
    user_id: int = Query(..., description="User ID"),
    account_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get account balance."""
    return account_service.get_balance(
        db=db,
        user_id=user_id,
        account_number=account_number,
        last4=last4,
        account_type=account_type,
    )


@router.get("/details")
def get_details(
    user_id: int = Query(..., description="User ID"),
    account_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get account details."""
    return account_service.get_details(
        db=db,
        user_id=user_id,
        account_number=account_number,
        last4=last4,
        account_type=account_type,
    )


@router.get("/status")
def get_status(
    user_id: int = Query(..., description="User ID"),
    account_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get account status."""
    return account_service.get_status(
        db=db,
        user_id=user_id,
        account_number=account_number,
        last4=last4,
        account_type=account_type,
    )


@router.get("/limits")
def get_limits(
    user_id: int = Query(..., description="User ID"),
    account_number: str | None = Query(None),
    last4: str | None = Query(None),
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get account limits."""
    return account_service.get_limits(
        db=db,
        user_id=user_id,
        account_number=account_number,
        last4=last4,
        account_type=account_type,
    )
