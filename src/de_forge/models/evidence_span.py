"""Evidence span persistence model."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class EvidenceSpan(Base):
    """Represents extracted evidence linked to a report chunk."""

    __tablename__ = "evidence_spans"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_chunk_id: Mapped[int] = mapped_column(ForeignKey("report_chunks.id"), nullable=False)
