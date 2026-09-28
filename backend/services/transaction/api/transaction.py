"""Transaction Service REST API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.transaction.db.database import get_db
from services.transaction.service.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

transaction_service = TransactionService()


@router.get("/")
def list_transactions(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(50, description="Max results"),
    offset: int = Query(0, description="Offset"),
    db: Session = Depends(get_db),
):
    """
    List all transactions for a user's accounts.

    Args:
        user_id: User ID (required)
        limit: Maximum results (default 50)
        offset: Result offset (default 0)
        db: Database session

    Returns:
        List of transactions
    """
    return transaction_service.list_transactions(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Get a specific transaction (with authorization check)."""
    return transaction_service.get_transaction(
        db=db,
        user_id=user_id,
        transaction_id=transaction_id,
    )


@router.get("/reference/{reference_number}")
def get_transaction_by_reference(
    reference_number: str,
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db),
):
    """Get transaction by reference number (with authorization check)."""
    return transaction_service.get_transaction(
        db=db,
        user_id=user_id,
        reference_number=reference_number,
    )
