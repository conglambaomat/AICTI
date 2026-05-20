"""Agent run persistence model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class AgentRun(Base):
    """Represents an execution trace for an agent run."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    output_hash: Mapped[str] = mapped_column(String(64), nullable=False)
