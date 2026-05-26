"""add artifact links

Revision ID: 20260527_02
Revises: 20260527_01
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260527_02"
down_revision: str | None = "20260527_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artifact_links",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("parent_artifact_id", sa.String(length=64), nullable=False),
        sa.Column("child_artifact_id", sa.String(length=64), nullable=False),
        sa.Column("link_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "parent_artifact_id != child_artifact_id", name="ck_artifact_links_no_self_link"
        ),
        sa.UniqueConstraint(
            "parent_artifact_id",
            "child_artifact_id",
            "link_type",
            name="uq_artifact_links_parent_child_type",
        ),
        sa.ForeignKeyConstraint(
            ["parent_artifact_id"],
            ["artifacts.id"],
            name="fk_artifact_links_parent_artifact_id_artifacts",
        ),
        sa.ForeignKeyConstraint(
            ["child_artifact_id"],
            ["artifacts.id"],
            name="fk_artifact_links_child_artifact_id_artifacts",
        ),
    )


def downgrade() -> None:
    op.drop_table("artifact_links")
