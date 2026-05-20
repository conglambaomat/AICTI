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
        sa.CheckConstraint("length(quote) > 0", name="ck_evidence_spans_quote_non_empty"),
        sa.CheckConstraint("char_start >= 0", name="ck_evidence_spans_char_start_gte_0"),
        sa.CheckConstraint(
            "char_end >= char_start", name="ck_evidence_spans_char_end_gte_char_start"
        ),
        sa.CheckConstraint(
            "length(supports_claim) > 0", name="ck_evidence_spans_supports_claim_non_empty"
        ),
        sa.CheckConstraint(
            "confidence >= 0 and confidence <= 1",
            name="ck_evidence_spans_confidence_between_0_and_1",
        ),
    )
    op.create_index("ix_evidence_spans_report_id", "evidence_spans", ["report_id"])
    op.create_index("ix_evidence_spans_chunk_id", "evidence_spans", ["chunk_id"])
    op.create_index("ix_evidence_spans_run_id", "evidence_spans", ["run_id"])

    op.create_table(
        "extracted_iocs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("evidence_id", sa.String(length=36), sa.ForeignKey("evidence_spans.id"), nullable=True),
        sa.Column("ioc_type", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("extractor", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint(
            "report_id", "ioc_type", "normalized_value", name="uq_extracted_iocs_report_type_normalized"
        ),
        sa.CheckConstraint(
            "ioc_type in ('ip', 'domain', 'hash', 'url', 'email', 'file_path')",
            name="ck_extracted_iocs_ioc_type_allowed",
        ),
        sa.CheckConstraint(
            "confidence >= 0 and confidence <= 1",
            name="ck_extracted_iocs_confidence_between_0_and_1",
        ),
    )
    op.create_index("ix_extracted_iocs_report_id", "extracted_iocs", ["report_id"])
    op.create_index("ix_extracted_iocs_ioc_type", "extracted_iocs", ["ioc_type"])
    op.create_index("ix_extracted_iocs_normalized_value", "extracted_iocs", ["normalized_value"])

    op.create_table("attack_mappings", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False), sa.Column("evidence_id", sa.String(length=36), sa.ForeignKey("evidence_spans.id"), nullable=False))
    op.create_table("telemetry_selections", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False), sa.Column("attack_mapping_id", sa.String(length=36), sa.ForeignKey("attack_mappings.id"), nullable=False))
    op.create_table("detection_specs", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("report_id", sa.String(length=36), sa.ForeignKey("reports.id"), nullable=False))
    op.create_table(
        "query_candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("detection_spec_id", sa.String(length=36), sa.ForeignKey("detection_specs.id"), nullable=False),
        sa.Column("query_id", sa.Text(), nullable=False),
        sa.Column("query_type", sa.Text(), nullable=False),
        sa.Column("query_language", sa.Text(), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("expected_signal", sa.Text(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.UniqueConstraint("detection_spec_id", "query_id", name="uq_query_candidates_spec_query_id"),
        sa.CheckConstraint(
            "query_type in ('high_precision', 'high_recall', 'balanced')",
            name="ck_query_candidates_query_type_allowed",
        ),
        sa.CheckConstraint(
            "query_language in ('kql', 'spl', 'eql')",
            name="ck_query_candidates_query_language_allowed",
        ),
    )
    op.create_index("ix_query_candidates_detection_spec_id", "query_candidates", ["detection_spec_id"])
    op.create_index("ix_query_candidates_selected", "query_candidates", ["selected"])
    op.create_index("ix_query_candidates_run_id", "query_candidates", ["run_id"])
    op.create_table("generated_rules", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("detection_spec_id", sa.String(length=36), sa.ForeignKey("detection_specs.id"), nullable=False), sa.Column("query_candidate_id", sa.String(length=36), sa.ForeignKey("query_candidates.id"), nullable=True))
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
    op.drop_index("ix_query_candidates_run_id", table_name="query_candidates")
    op.drop_index("ix_query_candidates_selected", table_name="query_candidates")
    op.drop_index("ix_query_candidates_detection_spec_id", table_name="query_candidates")
    op.drop_table("query_candidates")
    op.drop_table("detection_specs")
    op.drop_table("telemetry_selections")
    op.drop_table("attack_mappings")
    op.drop_index("ix_extracted_iocs_normalized_value", table_name="extracted_iocs")
    op.drop_index("ix_extracted_iocs_ioc_type", table_name="extracted_iocs")
    op.drop_index("ix_extracted_iocs_report_id", table_name="extracted_iocs")
    op.drop_table("extracted_iocs")
    op.drop_index("ix_evidence_spans_run_id", table_name="evidence_spans")
    op.drop_index("ix_evidence_spans_chunk_id", table_name="evidence_spans")
    op.drop_index("ix_evidence_spans_report_id", table_name="evidence_spans")
    op.drop_table("evidence_spans")
    op.drop_index("ix_report_chunks_report_id_chunk_index", table_name="report_chunks")
    op.drop_index("ix_report_chunks_report_id", table_name="report_chunks")
    op.drop_table("report_chunks")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_table("reports")
