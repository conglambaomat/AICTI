"""Report persistence model."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class Report(Base):
    """Represents an ingested threat report."""

    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("content_hash", name="uq_reports_content_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
