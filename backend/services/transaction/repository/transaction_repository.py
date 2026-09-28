from datetime import datetime
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from services.transaction.models.transaction import Transaction


class TransactionRepository:

    def get_by_id(
        self,
        db: Session,
        transaction_id: int,
    ) -> Transaction | None:

        return (
            db.query(Transaction)
            .filter(
                Transaction.id == transaction_id
            )
            .first()
        )

    def get_by_reference(
        self,
        db: Session,
        reference_number: str,
    ) -> Transaction | None:

        return (
            db.query(Transaction)
            .filter(
                Transaction.reference_number
                == reference_number
            )
            .first()
        )

    def list_by_account_ids(
        self,
        db: Session,
        account_ids: list[int],
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:

        if not account_ids:
            return []

        return (
            db.query(Transaction)
            .filter(
                or_(
                    Transaction.from_account_id.in_(
                        account_ids
                    ),
                    Transaction.to_account_id.in_(
                        account_ids
                    ),
                )
            )
            .order_by(
                Transaction.transaction_date.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def search(
        self,
        db: Session,
        account_ids: list[int],
        transaction_type: str | None = None,
        status: str | None = None,
        merchant_name: str | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:

        if not account_ids:
            return []

        query = (
            db.query(Transaction)
            .filter(
                or_(
                    Transaction.from_account_id.in_(
                        account_ids
                    ),
                    Transaction.to_account_id.in_(
                        account_ids
                    ),
                )
            )
        )

        if transaction_type:
            query = query.filter(
                Transaction.transaction_type
                == transaction_type.upper()
            )

        if status:
            query = query.filter(
                Transaction.status
                == status.upper()
            )

        if merchant_name:
            query = query.filter(
                Transaction.merchant_name.ilike(
                    f"%{merchant_name}%"
                )
            )

        if min_amount is not None:
            query = query.filter(
                Transaction.amount >= min_amount
            )

        if max_amount is not None:
            query = query.filter(
                Transaction.amount <= max_amount
            )

        if start_date:
            query = query.filter(
                Transaction.transaction_date
                >= start_date
            )

        if end_date:
            query = query.filter(
                Transaction.transaction_date
                <= end_date
            )

        return (
            query
            .order_by(
                Transaction.transaction_date.desc()
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_pending(
        self,
        db: Session,
        account_ids: list[int],
        limit: int = 50,
    ) -> list[Transaction]:

        if not account_ids:
            return []

        return (
            db.query(Transaction)
            .filter(
                or_(
                    Transaction.from_account_id.in_(
                        account_ids
                    ),
                    Transaction.to_account_id.in_(
                        account_ids
                    ),
                ),
                Transaction.status == "PENDING",
            )
            .order_by(
                Transaction.transaction_date.desc()
            )
            .limit(limit)
            .all()
        )

    def update_dispute(
        self,
        db: Session,
        transaction_id: int,
        dispute_status: str,
        dispute_reason: str | None = None,
    ) -> Transaction | None:

        transaction = self.get_by_id(
            db=db,
            transaction_id=transaction_id,
        )

        if not transaction:
            return None

        transaction.dispute_status = dispute_status

        if dispute_reason is not None:
            transaction.dispute_reason = dispute_reason

        db.commit()
        db.refresh(transaction)

        return transaction