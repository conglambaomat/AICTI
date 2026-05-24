"""Harden review_decisions schema with strict fail-closed checks.

Revision ID: 20260523_02
Revises: 20260520_01
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260523_02"
down_revision = "20260520_01"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _fail_if_legacy_rows_exist(connection: sa.Connection) -> None:
    row_count = connection.execute(sa.text("SELECT COUNT(*) FROM review_decisions")).scalar_one()
    if row_count and row_count > 0:
        raise RuntimeError(
            "strict fail-closed migration blocked: review_decisions contains legacy rows without "
            "decision/reviewer/created_at. Manual data remediation is required before upgrade."
        )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    has_decision = _has_column(inspector, "review_decisions", "decision")
    has_reviewer = _has_column(inspector, "review_decisions", "reviewer")
    has_created_at = _has_column(inspector, "review_decisions", "created_at")

    if has_decision and has_reviewer and has_created_at:
        return

    _fail_if_legacy_rows_exist(bind)

    with op.batch_alter_table("review_decisions") as batch_op:
        if not has_decision:
            batch_op.add_column(sa.Column("decision", sa.String(length=20), nullable=False))
        if not has_reviewer:
            batch_op.add_column(sa.Column("reviewer", sa.String(length=120), nullable=False))
        if not has_created_at:
            batch_op.add_column(sa.Column("created_at", sa.String(length=40), nullable=False))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    has_decision = _has_column(inspector, "review_decisions", "decision")
    has_reviewer = _has_column(inspector, "review_decisions", "reviewer")
    has_created_at = _has_column(inspector, "review_decisions", "created_at")

    with op.batch_alter_table("review_decisions") as batch_op:
        if has_created_at:
            batch_op.drop_column("created_at")
        if has_reviewer:
            batch_op.drop_column("reviewer")
        if has_decision:
            batch_op.drop_column("decision")
