"""Database session factory utilities."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Session:
    """Provide a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
