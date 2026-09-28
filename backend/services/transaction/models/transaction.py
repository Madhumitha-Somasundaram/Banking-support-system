from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)

from services.transaction.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Logical reference to account_db.accounts
    from_account_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    # Logical reference to account_db.accounts
    to_account_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    transaction_type = Column(
        String(30),
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="COMPLETED",
    )

    description = Column(
        String(255),
        nullable=True,
    )

    merchant_name = Column(
        String(255),
        nullable=True,
    )

    reference_number = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    transaction_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    dispute_status = Column(
        String(30),
        nullable=False,
        default="NONE",
    )

    dispute_reason = Column(
        Text,
        nullable=True,
    )