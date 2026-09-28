from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Numeric
)

from services.card.db.database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    account_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    card_number = Column(
        String(20),
        unique=True,
        nullable=False,
    )

    card_type = Column(
        String(30),
        nullable=False,
    )

    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
    )

    expiry_date = Column(
        DateTime,
        nullable=False,
    )

    daily_purchase_limit = Column(
    Numeric(12, 2),
    nullable=False,
    default=5000,
)

    daily_atm_limit = Column(
    Numeric(12, 2),
    nullable=False,
    default=1000,
)

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )