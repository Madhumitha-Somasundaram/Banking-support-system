"""
Card Service Database Module

Separate database for Card domain (separate from main User/Auth DB).
Uses dedicated CARD_DATABASE_URL configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from shared.config import settings

# Card Service DB Engine
engine = create_engine(
    settings.CARD_DATABASE_URL,
    echo=False
)

# Card Service Session Factory
SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

# Card Service ORM Base
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
