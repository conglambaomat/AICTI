"""add evidence retrieval links

Revision ID: 20260527_03
Revises: 20260527_02
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260527_03"
down_revision: str | None = "20260527_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_retrieval_links",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_id", sa.String(length=36), nullable=False),
        sa.Column("retrieval_candidate_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(
            ["evidence_id"],
            ["evidence_spans.id"],
            name="fk_evidence_retrieval_links_evidence_id_evidence_spans",
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_candidate_id"],
            ["retrieval_candidates.id"],
            name="fk_evidence_retrieval_links_retrieval_candidate_id_retrieval_candidates",
        ),
        sa.UniqueConstraint(
            "run_id",
            "evidence_id",
            "retrieval_candidate_id",
            name="uq_evidence_retrieval_links_run_evidence_candidate",
        ),
    )
    op.create_index(
        "ix_evidence_retrieval_links_run_id", "evidence_retrieval_links", ["run_id"]
    )
    op.create_index(
        "ix_evidence_retrieval_links_evidence_id", "evidence_retrieval_links", ["evidence_id"]
    )
    op.create_index(
        "ix_evidence_retrieval_links_retrieval_candidate_id",
        "evidence_retrieval_links",
        ["retrieval_candidate_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evidence_retrieval_links_retrieval_candidate_id",
        table_name="evidence_retrieval_links",
    )
    op.drop_index(
        "ix_evidence_retrieval_links_evidence_id", table_name="evidence_retrieval_links"
    )
    op.drop_index("ix_evidence_retrieval_links_run_id", table_name="evidence_retrieval_links")
    op.drop_table("evidence_retrieval_links")
