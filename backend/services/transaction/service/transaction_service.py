from datetime import datetime
from decimal import Decimal
from enum import Enum

import httpx
from sqlalchemy.orm import Session

from shared.config import settings
from services.transaction.repository.transaction_repository import (
    TransactionRepository,
)


class TransactionResolutionStatus(str, Enum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID = "INVALID"


class TransactionService:

    def __init__(self):
        self.transaction_repository = TransactionRepository()

    # ---------------------------------------------------------
    # Account ownership (via Account Service)
    # ---------------------------------------------------------

    def _get_user_account_ids(
        self,
        db: Session,
        user_id: int,
    ) -> list[int]:
        """
        Get account IDs for a user by calling Account Service.

        This verifies account ownership via the Account Service HTTP API
        instead of querying the account_repository directly (which is now
        in a separate microservice).
        """
        try:
            url = f"{settings.ACCOUNT_SERVICE_URL}/accounts/"
            with httpx.Client() as client:
                response = client.get(
                    url,
                    params={"user_id": user_id},
                    timeout=10.0,
                )
                response.raise_for_status()
                accounts = response.json()

                return [
                    account["account_id"]
                    for account in accounts
                ]
        except httpx.HTTPError:
            # If Account Service unavailable, return empty list
            # This prevents transaction access if we can't verify ownership
            return []

    # ---------------------------------------------------------
    # Formatting
    # ---------------------------------------------------------

    @staticmethod
    def _format_transaction(
        transaction,
        account_ids: list[int],
    ) -> dict:

        direction = "UNKNOWN"

        if transaction.from_account_id in account_ids:
            direction = "OUTGOING"

        if transaction.to_account_id in account_ids:
            direction = "INCOMING"

        return {
            "transaction_id": transaction.id,
            "reference_number": (
                transaction.reference_number
            ),
            "from_account_id": (
                transaction.from_account_id
            ),
            "to_account_id": (
                transaction.to_account_id
            ),
            "transaction_type": (
                transaction.transaction_type
            ),
            "amount": float(transaction.amount),
            "status": transaction.status,
            "direction": direction,
            "description": transaction.description,
            "merchant_name": transaction.merchant_name,
            "transaction_date": (
                transaction.transaction_date.isoformat()
                if transaction.transaction_date
                else None
            ),
            "dispute_status": (
                transaction.dispute_status
            ),
        }

    # ---------------------------------------------------------
    # Get one transaction
    # ---------------------------------------------------------

    def get_transaction(
        self,
        db: Session,
        user_id: int,
        transaction_id: int | None = None,
        reference_number: str | None = None,
    ) -> dict:

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        if not account_ids:
            return {
                "status": TransactionResolutionStatus.NOT_FOUND,
                "message": "Transaction not found.",
            }

        transaction = None

        if transaction_id is not None:
            transaction = (
                self.transaction_repository.get_by_id(
                    db=db,
                    transaction_id=transaction_id,
                )
            )

        elif reference_number:
            transaction = (
                self.transaction_repository.get_by_reference(
                    db=db,
                    reference_number=reference_number,
                )
            )

        else:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": (
                    "Transaction ID or reference number "
                    "is required."
                ),
            }

        if not transaction:
            return {
                "status": TransactionResolutionStatus.NOT_FOUND,
                "message": "Transaction not found.",
            }

        # IMPORTANT:
        # Check ownership AFTER retrieving the transaction.
        if (
            transaction.from_account_id not in account_ids
            and transaction.to_account_id not in account_ids
        ):
            return {
                "status": TransactionResolutionStatus.NOT_FOUND,
                "message": "Transaction not found.",
            }

        return {
            "status": TransactionResolutionStatus.FOUND,
            "transaction": self._format_transaction(
                transaction,
                account_ids,
            ),
        }

    # ---------------------------------------------------------
    # List transactions
    # ---------------------------------------------------------

    def list_transactions(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:

        if limit < 1 or limit > 100:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "Limit must be between 1 and 100.",
            }

        if offset < 0:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "Offset cannot be negative.",
            }

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        transactions = (
            self.transaction_repository.list_by_account_ids(
                db=db,
                account_ids=account_ids,
                limit=limit,
                offset=offset,
            )
        )

        return {
            "status": "FOUND",
            "count": len(transactions),
            "transactions": [
                self._format_transaction(
                    transaction,
                    account_ids,
                )
                for transaction in transactions
            ],
        }

    # ---------------------------------------------------------
    # Search transactions
    # ---------------------------------------------------------

    def search_transactions(
        self,
        db: Session,
        user_id: int,
        transaction_type: str | None = None,
        status: str | None = None,
        merchant_name: str | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:

        if limit < 1 or limit > 100:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "Limit must be between 1 and 100.",
            }

        if offset < 0:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "Offset cannot be negative.",
            }

        if (
            min_amount is not None
            and max_amount is not None
            and min_amount > max_amount
        ):
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": (
                    "Minimum amount cannot be greater "
                    "than maximum amount."
                ),
            }

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": (
                    "Start date cannot be after end date."
                ),
            }

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        transactions = (
            self.transaction_repository.search(
                db=db,
                account_ids=account_ids,
                transaction_type=transaction_type,
                status=status,
                merchant_name=merchant_name,
                min_amount=min_amount,
                max_amount=max_amount,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
            )
        )

        return {
            "status": "FOUND",
            "count": len(transactions),
            "transactions": [
                self._format_transaction(
                    transaction,
                    account_ids,
                )
                for transaction in transactions
            ],
        }

    # ---------------------------------------------------------
    # Pending transactions
    # ---------------------------------------------------------

    def get_pending_transactions(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
    ) -> dict:

        if limit < 1 or limit > 100:
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "Limit must be between 1 and 100.",
            }

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        transactions = (
            self.transaction_repository.list_pending(
                db=db,
                account_ids=account_ids,
                limit=limit,
            )
        )

        return {
            "status": "FOUND",
            "count": len(transactions),
            "transactions": [
                self._format_transaction(
                    transaction,
                    account_ids,
                )
                for transaction in transactions
            ],
        }

    # ---------------------------------------------------------
    # Transaction summary
    # ---------------------------------------------------------

    def get_transaction_summary(
        self,
        db: Session,
        user_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        transactions = (
            self.transaction_repository.search(
                db=db,
                account_ids=account_ids,
                start_date=start_date,
                end_date=end_date,
                limit=100,
                offset=0,
            )
        )

        total_incoming = Decimal("0")
        total_outgoing = Decimal("0")

        incoming_count = 0
        outgoing_count = 0

        for transaction in transactions:

            amount = Decimal(
                str(transaction.amount)
            )

            if transaction.to_account_id in account_ids:
                total_incoming += amount
                incoming_count += 1

            if transaction.from_account_id in account_ids:
                total_outgoing += amount
                outgoing_count += 1

        return {
            "status": "FOUND",
            "period": {
                "start_date": (
                    start_date.isoformat()
                    if start_date
                    else None
                ),
                "end_date": (
                    end_date.isoformat()
                    if end_date
                    else None
                ),
            },
            "incoming": {
                "count": incoming_count,
                "total": float(total_incoming),
            },
            "outgoing": {
                "count": outgoing_count,
                "total": float(total_outgoing),
            },
        }

    # ---------------------------------------------------------
    # Dispute transaction
    # ---------------------------------------------------------

    def dispute_transaction(
        self,
        db: Session,
        user_id: int,
        transaction_id: int,
        reason: str,
    ) -> dict:

        if not reason or not reason.strip():
            return {
                "status": TransactionResolutionStatus.INVALID,
                "message": "A dispute reason is required.",
            }

        account_ids = self._get_user_account_ids(
            db=db,
            user_id=user_id,
        )

        transaction = (
            self.transaction_repository.get_by_id(
                db=db,
                transaction_id=transaction_id,
            )
        )

        if not transaction:
            return {
                "status": TransactionResolutionStatus.NOT_FOUND,
                "message": "Transaction not found.",
            }

        if (
            transaction.from_account_id not in account_ids
            and transaction.to_account_id not in account_ids
        ):
            return {
                "status": TransactionResolutionStatus.NOT_FOUND,
                "message": "Transaction not found.",
            }

        if transaction.dispute_status != "NONE":
            return {
                "status": "INVALID",
                "message": (
                    "This transaction already has "
                    "a dispute request."
                ),
            }

        updated = (
            self.transaction_repository.update_dispute(
                db=db,
                transaction_id=transaction_id,
                dispute_status="REQUESTED",
                dispute_reason=reason.strip(),
            )
        )

        return {
            "status": "REQUESTED",
            "transaction": self._format_transaction(
                updated,
                account_ids,
            ),
        }