"""Database session factory utilities."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=settings.database_pool_pre_ping,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
