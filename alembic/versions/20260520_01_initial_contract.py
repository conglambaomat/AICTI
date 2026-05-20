"""initial persistence contract

Revision ID: 20260520_01
Revises:
Create Date: 2026-05-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260520_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ingested"),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("content_hash", name="uq_reports_content_hash"),
    )
    op.create_index("ix_reports_created_at", "reports", ["created_at"])
    op.create_index("ix_reports_status", "reports", ["status"])

    op.create_table(
        "report_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("chunk_type", sa.String(length=20), nullable=False, server_default="paragraph"),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("report_id", "chunk_index", name="uq_report_chunks_report_chunk_index"),
        sa.CheckConstraint("char_start <= char_end", name="ck_report_chunks_char_start_lte_char_end"),
        sa.CheckConstraint("char_start >= 0", name="ck_report_chunks_char_start_gte_0"),
    )
    op.create_index("ix_report_chunks_report_id", "report_chunks", ["report_id"])
    op.create_index("ix_report_chunks_report_id_chunk_index", "report_chunks", ["report_id", "chunk_index"])

    op.create_table(
        "evidence_spans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("chunk_id", sa.String(length=36), sa.ForeignKey("report_chunks.id"), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("supports_claim", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_by_agent", sa.Text(), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
    )

    op.create_table("attack_mappings", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False), sa.Column("evidence_id", sa.String(length=36), sa.ForeignKey("evidence_spans.id"), nullable=False))
    op.create_table("telemetry_selections", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False), sa.Column("attack_mapping_id", sa.String(length=36), sa.ForeignKey("attack_mappings.id"), nullable=False))
    op.create_table("detection_specs", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False))
    op.create_table("generated_rules", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("detection_spec_id", sa.String(length=36), sa.ForeignKey("detection_specs.id"), nullable=False))
    op.create_table("validation_results", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False))
    op.create_table("test_runs", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False))
    op.create_table("agent_runs", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("run_id", sa.String(length=36), nullable=False), sa.Column("trace_id", sa.String(length=36), nullable=False), sa.Column("agent_name", sa.Text(), nullable=False), sa.Column("input_hash", sa.Text(), nullable=False), sa.Column("output_hash", sa.Text(), nullable=True), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("retry_attempt", sa.Integer(), nullable=False, server_default="0"), sa.Column("started_at", sa.String(length=40), nullable=False))
    op.create_table("review_decisions", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=False))
    op.create_table("refinement_iterations", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("detection_spec_id", sa.String(length=36), sa.ForeignKey("detection_specs.id"), nullable=True), sa.Column("rule_id", sa.String(length=36), sa.ForeignKey("generated_rules.id"), nullable=True))


def downgrade() -> None:
    op.drop_table("refinement_iterations")
    op.drop_table("review_decisions")
    op.drop_table("agent_runs")
    op.drop_table("test_runs")
    op.drop_table("validation_results")
    op.drop_table("generated_rules")
    op.drop_table("detection_specs")
    op.drop_table("telemetry_selections")
    op.drop_table("attack_mappings")
    op.drop_table("evidence_spans")
    op.drop_index("ix_report_chunks_report_id_chunk_index", table_name="report_chunks")
    op.drop_index("ix_report_chunks_report_id", table_name="report_chunks")
    op.drop_table("report_chunks")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_table("reports")
