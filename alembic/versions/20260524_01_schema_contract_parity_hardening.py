"""Align Alembic schema with current persistence models.

Revision ID: 20260524_01
Revises: 20260523_04
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260524_01"
down_revision = "20260523_04"
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    with op.batch_alter_table("detection_specs") as batch_op:
        if not _has_column(inspector, "detection_specs", "abstain_code"):
            batch_op.add_column(sa.Column("abstain_code", sa.String(length=80), nullable=True))
        if not _has_column(inspector, "detection_specs", "abstain_context"):
            batch_op.add_column(sa.Column("abstain_context", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "abstain_human_message"):
            batch_op.add_column(sa.Column("abstain_human_message", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "spec_payload"):
            batch_op.add_column(sa.Column("spec_payload", sa.Text(), nullable=True))
        if not _has_column(inspector, "detection_specs", "is_validated"):
            batch_op.add_column(sa.Column("is_validated", sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table("generated_rules") as batch_op:
        if not _has_column(inspector, "generated_rules", "rule_content"):
            batch_op.add_column(sa.Column("rule_content", sa.Text(), nullable=True))

    inspector = sa.inspect(bind)

    if not _has_table(inspector, "pipeline_runs"):
        op.create_table(
            "pipeline_runs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), nullable=False, unique=True),
            sa.Column("report_id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("stage", sa.String(length=40), nullable=False),
            sa.Column("detection_spec_id", sa.String(length=36), nullable=True),
            sa.Column("rule_id", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.String(length=40), nullable=False),
        )

    if not _has_table(inspector, "proof_obligations"):
        op.create_table(
            "proof_obligations",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), nullable=False),
            sa.Column("rule_candidate_id", sa.String(length=36), nullable=False),
            sa.Column("claim_type", sa.String(length=64), nullable=False),
            sa.Column("claim_text", sa.Text(), nullable=False),
            sa.Column("required_artifact_types", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("justification", sa.Text(), nullable=True),
        )

    if not _has_table(inspector, "candidate_scores"):
        op.create_table(
            "candidate_scores",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("score_type", sa.String(length=64), nullable=False),
            sa.Column("score_value", sa.Float(), nullable=False),
            sa.Column("score_breakdown_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint("score_value >= 0 and score_value <= 1", name="ck_candidate_scores_score_value_between_0_and_1"),
            sa.CheckConstraint("length(score_type) > 0", name="ck_candidate_scores_score_type_non_empty"),
        )

    if not _has_table(inspector, "oracle_evaluation_results"):
        op.create_table(
            "oracle_evaluation_results",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("oracle_case_id", sa.String(length=80), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint("score >= 0 and score <= 1", name="ck_oracle_evaluation_results_score_between_0_and_1"),
            sa.CheckConstraint("length(oracle_case_id) > 0", name="ck_oracle_evaluation_results_oracle_case_id_non_empty"),
        )

    if not _has_table(inspector, "regression_runs"):
        op.create_table(
            "regression_runs",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="unknown"),
            sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint("status in ('passed', 'failed', 'unknown')", name="ck_regression_runs_status_allowed"),
        )

    if not _has_table(inspector, "quality_snapshots"):
        op.create_table(
            "quality_snapshots",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("run_id", sa.String(length=36), sa.ForeignKey("pipeline_runs.run_id"), nullable=False),
            sa.Column("snapshot_type", sa.String(length=64), nullable=False),
            sa.Column("metrics_json", sa.Text(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.CheckConstraint("length(snapshot_type) > 0", name="ck_quality_snapshots_snapshot_type_non_empty"),
        )

    inspector = sa.inspect(bind)
    indexes = {
        "pipeline_runs": [
            ("ix_pipeline_runs_run_id", ["run_id"]),
            ("ix_pipeline_runs_report_id", ["report_id"]),
            ("ix_pipeline_runs_detection_spec_id", ["detection_spec_id"]),
        ],
        "proof_obligations": [
            ("ix_proof_obligations_rule_candidate_id", ["rule_candidate_id"]),
            ("ix_proof_obligations_run_id", ["run_id"]),
        ],
        "candidate_scores": [
            ("ix_candidate_scores_rule_id", ["rule_id"]),
            ("ix_candidate_scores_run_id", ["run_id"]),
        ],
        "oracle_evaluation_results": [
            ("ix_oracle_evaluation_results_rule_id", ["rule_id"]),
            ("ix_oracle_evaluation_results_run_id", ["run_id"]),
        ],
        "regression_runs": [
            ("ix_regression_runs_rule_id", ["rule_id"]),
            ("ix_regression_runs_run_id", ["run_id"]),
        ],
        "quality_snapshots": [("ix_quality_snapshots_run_id", ["run_id"])],
    }
    for table_name, table_indexes in indexes.items():
        if _has_table(inspector, table_name):
            for index_name, columns in table_indexes:
                if not _has_index(inspector, table_name, index_name):
                    op.create_index(index_name, table_name, columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, index_name in (
        ("quality_snapshots", "ix_quality_snapshots_run_id"),
        ("regression_runs", "ix_regression_runs_run_id"),
        ("regression_runs", "ix_regression_runs_rule_id"),
        ("oracle_evaluation_results", "ix_oracle_evaluation_results_run_id"),
        ("oracle_evaluation_results", "ix_oracle_evaluation_results_rule_id"),
        ("candidate_scores", "ix_candidate_scores_run_id"),
        ("candidate_scores", "ix_candidate_scores_rule_id"),
        ("proof_obligations", "ix_proof_obligations_run_id"),
        ("proof_obligations", "ix_proof_obligations_rule_candidate_id"),
        ("pipeline_runs", "ix_pipeline_runs_detection_spec_id"),
        ("pipeline_runs", "ix_pipeline_runs_report_id"),
        ("pipeline_runs", "ix_pipeline_runs_run_id"),
    ):
        if _has_table(inspector, table_name) and _has_index(inspector, table_name, index_name):
            op.drop_index(index_name, table_name=table_name)

    for table_name in (
        "quality_snapshots",
        "regression_runs",
        "oracle_evaluation_results",
        "candidate_scores",
        "proof_obligations",
        "pipeline_runs",
    ):
        inspector = sa.inspect(bind)
        if _has_table(inspector, table_name):
            op.drop_table(table_name)

    inspector = sa.inspect(bind)
    with op.batch_alter_table("generated_rules") as batch_op:
        if _has_column(inspector, "generated_rules", "rule_content"):
            batch_op.drop_column("rule_content")

    with op.batch_alter_table("detection_specs") as batch_op:
        for column_name in (
            "is_validated",
            "spec_payload",
            "abstain_human_message",
            "abstain_context",
            "abstain_code",
        ):
            if _has_column(inspector, "detection_specs", column_name):
                batch_op.drop_column(column_name)
