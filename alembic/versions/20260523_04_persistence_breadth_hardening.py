"""Harden persistence breadth for lineage-heavy Section 20 domains.

Revision ID: 20260523_04
Revises: 20260523_03
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260523_04"
down_revision = "20260523_03"
branch_labels = None
depends_on = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    with op.batch_alter_table("validation_results") as batch_op:
        if not _has_column(inspector, "validation_results", "run_id"):
            batch_op.add_column(sa.Column("run_id", sa.String(length=36), nullable=False, server_default="run_unknown"))
        if not _has_column(inspector, "validation_results", "status"):
            batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"))
        if not _has_column(inspector, "validation_results", "details_json"):
            batch_op.add_column(sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"))
        if not _has_column(inspector, "validation_results", "created_at"):
            batch_op.add_column(sa.Column("created_at", sa.String(length=40), nullable=False, server_default="1970-01-01T00:00:00+00:00"))

    with op.batch_alter_table("test_runs") as batch_op:
        if not _has_column(inspector, "test_runs", "run_id"):
            batch_op.add_column(sa.Column("run_id", sa.String(length=36), nullable=False, server_default="run_unknown"))
        if not _has_column(inspector, "test_runs", "status"):
            batch_op.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"))
        if not _has_column(inspector, "test_runs", "result_json"):
            batch_op.add_column(sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"))
        if not _has_column(inspector, "test_runs", "created_at"):
            batch_op.add_column(sa.Column("created_at", sa.String(length=40), nullable=False, server_default="1970-01-01T00:00:00+00:00"))

    with op.batch_alter_table("review_decisions") as batch_op:
        if not _has_column(inspector, "review_decisions", "run_id"):
            batch_op.add_column(sa.Column("run_id", sa.String(length=36), nullable=False, server_default="run_unknown"))
        if not _has_column(inspector, "review_decisions", "comments"):
            batch_op.add_column(sa.Column("comments", sa.Text(), nullable=False, server_default=""))

    with op.batch_alter_table("refinement_iterations") as batch_op:
        if not _has_column(inspector, "refinement_iterations", "run_id"):
            batch_op.add_column(sa.Column("run_id", sa.String(length=36), nullable=False, server_default="run_unknown"))
        if not _has_column(inspector, "refinement_iterations", "feedback_ref"):
            batch_op.add_column(sa.Column("feedback_ref", sa.Text(), nullable=False, server_default=""))
        if not _has_column(inspector, "refinement_iterations", "regression_ref"):
            batch_op.add_column(sa.Column("regression_ref", sa.Text(), nullable=False, server_default=""))
        if not _has_column(inspector, "refinement_iterations", "created_at"):
            batch_op.add_column(sa.Column("created_at", sa.String(length=40), nullable=False, server_default="1970-01-01T00:00:00+00:00"))

    inspector = sa.inspect(bind)

    if not _has_index(inspector, "validation_results", "ix_validation_results_rule_id"):
        op.create_index("ix_validation_results_rule_id", "validation_results", ["rule_id"])
    if not _has_index(inspector, "validation_results", "ix_validation_results_run_id"):
        op.create_index("ix_validation_results_run_id", "validation_results", ["run_id"])

    if not _has_index(inspector, "test_runs", "ix_test_runs_rule_id"):
        op.create_index("ix_test_runs_rule_id", "test_runs", ["rule_id"])
    if not _has_index(inspector, "test_runs", "ix_test_runs_run_id"):
        op.create_index("ix_test_runs_run_id", "test_runs", ["run_id"])

    if not _has_index(inspector, "review_decisions", "ix_review_decisions_rule_id"):
        op.create_index("ix_review_decisions_rule_id", "review_decisions", ["rule_id"])
    if not _has_index(inspector, "review_decisions", "ix_review_decisions_run_id"):
        op.create_index("ix_review_decisions_run_id", "review_decisions", ["run_id"])

    if not _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_detection_spec_id"):
        op.create_index(
            "ix_refinement_iterations_detection_spec_id",
            "refinement_iterations",
            ["detection_spec_id"],
        )
    if not _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_rule_id"):
        op.create_index("ix_refinement_iterations_rule_id", "refinement_iterations", ["rule_id"])
    if not _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_run_id"):
        op.create_index("ix_refinement_iterations_run_id", "refinement_iterations", ["run_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_run_id"):
        op.drop_index("ix_refinement_iterations_run_id", table_name="refinement_iterations")
    if _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_rule_id"):
        op.drop_index("ix_refinement_iterations_rule_id", table_name="refinement_iterations")
    if _has_index(inspector, "refinement_iterations", "ix_refinement_iterations_detection_spec_id"):
        op.drop_index("ix_refinement_iterations_detection_spec_id", table_name="refinement_iterations")

    if _has_index(inspector, "review_decisions", "ix_review_decisions_run_id"):
        op.drop_index("ix_review_decisions_run_id", table_name="review_decisions")
    if _has_index(inspector, "review_decisions", "ix_review_decisions_rule_id"):
        op.drop_index("ix_review_decisions_rule_id", table_name="review_decisions")

    if _has_index(inspector, "test_runs", "ix_test_runs_run_id"):
        op.drop_index("ix_test_runs_run_id", table_name="test_runs")
    if _has_index(inspector, "test_runs", "ix_test_runs_rule_id"):
        op.drop_index("ix_test_runs_rule_id", table_name="test_runs")

    if _has_index(inspector, "validation_results", "ix_validation_results_run_id"):
        op.drop_index("ix_validation_results_run_id", table_name="validation_results")
    if _has_index(inspector, "validation_results", "ix_validation_results_rule_id"):
        op.drop_index("ix_validation_results_rule_id", table_name="validation_results")

    with op.batch_alter_table("refinement_iterations") as batch_op:
        if _has_column(inspector, "refinement_iterations", "created_at"):
            batch_op.drop_column("created_at")
        if _has_column(inspector, "refinement_iterations", "regression_ref"):
            batch_op.drop_column("regression_ref")
        if _has_column(inspector, "refinement_iterations", "feedback_ref"):
            batch_op.drop_column("feedback_ref")
        if _has_column(inspector, "refinement_iterations", "run_id"):
            batch_op.drop_column("run_id")

    with op.batch_alter_table("review_decisions") as batch_op:
        if _has_column(inspector, "review_decisions", "comments"):
            batch_op.drop_column("comments")
        if _has_column(inspector, "review_decisions", "run_id"):
            batch_op.drop_column("run_id")

    with op.batch_alter_table("test_runs") as batch_op:
        if _has_column(inspector, "test_runs", "created_at"):
            batch_op.drop_column("created_at")
        if _has_column(inspector, "test_runs", "result_json"):
            batch_op.drop_column("result_json")
        if _has_column(inspector, "test_runs", "status"):
            batch_op.drop_column("status")
        if _has_column(inspector, "test_runs", "run_id"):
            batch_op.drop_column("run_id")

    with op.batch_alter_table("validation_results") as batch_op:
        if _has_column(inspector, "validation_results", "created_at"):
            batch_op.drop_column("created_at")
        if _has_column(inspector, "validation_results", "details_json"):
            batch_op.drop_column("details_json")
        if _has_column(inspector, "validation_results", "status"):
            batch_op.drop_column("status")
        if _has_column(inspector, "validation_results", "run_id"):
            batch_op.drop_column("run_id")
