"""
Account Service Models

Note: user_id is a logical reference (NOT a foreign key) to the User table
in the main application database. There is NO foreign key constraint because
the users table is in a separate database.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Numeric, String,ForeignKey

from services.account.db.database import Base


class AccountType(Base):
    __tablename__ = "account_types"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(30),
        unique=True,
        nullable=False,
    )

    daily_transfer_limit = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    daily_withdrawal_limit = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    monthly_transfer_limit = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Logical reference to User (NOT a foreign key - different database)
    user_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    account_type_id = Column(
    Integer,
    ForeignKey("account_types.id"),
    nullable=False,
    index=True,
)

    account_number = Column(
        String(20),
        unique=True,
        nullable=False,
    )

    balance = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
    )

    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    opened_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
