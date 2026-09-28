from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from shared.config import settings

engine=create_engine(
    settings.DATABASE_URL,
    echo=False
)

SessionLocal=sessionmaker(
    autoflush=False ,
    autocommit=False,
    bind=engine
)

Base=declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()