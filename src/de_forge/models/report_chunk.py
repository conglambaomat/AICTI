"""Report chunk persistence model."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class ReportChunk(Base):
    """Represents a chunk extracted from a report."""

    __tablename__ = "report_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
