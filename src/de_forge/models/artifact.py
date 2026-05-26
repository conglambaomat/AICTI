from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    output_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parent_artifact_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ArtifactLink(Base):
    __tablename__ = "artifact_links"
    __table_args__ = (
        CheckConstraint(
            "parent_artifact_id != child_artifact_id", name="ck_artifact_links_no_self_link"
        ),
        UniqueConstraint(
            "parent_artifact_id",
            "child_artifact_id",
            "link_type",
            name="uq_artifact_links_parent_child_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    parent_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", name="fk_artifact_links_parent_artifact_id_artifacts"),
        nullable=False,
    )
    child_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("artifacts.id", name="fk_artifact_links_child_artifact_id_artifacts"),
        nullable=False,
    )
    link_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
