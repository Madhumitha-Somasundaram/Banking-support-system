"""
Transaction Service Database Module

Separate database for Transaction domain (separate from main User/Auth DB).
Uses dedicated TRANSACTION_DATABASE_URL configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from shared.config import settings

# Transaction Service DB Engine
engine = create_engine(
    settings.TRANSACTION_DATABASE_URL,
    echo=False
)

# Transaction Service Session Factory
SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

# Transaction Service ORM Base
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
