"""
Account Service Database Module

Separate database for Account domain (separate from main User/Auth DB).
Uses dedicated ACCOUNT_DATABASE_URL configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from shared.config import settings

# Account Service DB Engine
engine = create_engine(
    settings.ACCOUNT_DATABASE_URL,
    echo=False
)

# Account Service Session Factory
SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

# Account Service ORM Base
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
