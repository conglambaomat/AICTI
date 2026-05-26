"""Add generated rule provenance columns."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260526_01"
down_revision = "20260524_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_rules",
        sa.Column(
            "generation_source",
            sa.String(length=30),
            nullable=False,
            server_default="manual_draft",
        ),
    )
    op.add_column(
        "generated_rules",
        sa.Column("detection_ast_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "generated_rules",
        sa.Column("compiled_sigma_id", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_rules", "compiled_sigma_id")
    op.drop_column("generated_rules", "detection_ast_id")
    op.drop_column("generated_rules", "generation_source")
