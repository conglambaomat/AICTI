"""Core persistence contract models."""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base

GRAPH_NODE_TYPE_CHECK = (
    "node_type in ('report', 'chunk', 'evidence_quote', 'behavior', "
    "'attack_technique', 'detection_strategy', 'analytic', 'data_component', "
    "'telemetry_source', 'telemetry_field', 'detection_spec', 'detection_ast', "
    "'compiled_sigma', 'generated_rule', 'validation_result', 'proof_obligation', "
    "'review_decision', 'feedback_pattern', 'regression_test')"
)

GRAPH_EDGE_TYPE_CHECK = (
    "edge_type in ('supports', 'mentions', 'maps_to', 'requires', 'implements', "
    "'validated_by', 'derived_from', 'satisfies', 'failed_by', 'contradicts')"
)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_reports_content_hash"),
        Index("ix_reports_created_at", "created_at"),
        Index("ix_reports_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_uri: Mapped[str | None] = mapped_column(Text())
    title: Mapped[str | None] = mapped_column(Text())
    raw_text: Mapped[str] = mapped_column(Text(), nullable=False)
    content_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ingested")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)


class ReportChunk(Base):
    __tablename__ = "report_chunks"
    __table_args__ = (
        UniqueConstraint("report_id", "chunk_index", name="uq_report_chunks_report_chunk_index"),
        CheckConstraint("char_start <= char_end", name="ck_report_chunks_char_start_lte_char_end"),
        CheckConstraint("char_start >= 0", name="ck_report_chunks_char_start_gte_0"),
        Index("ix_report_chunks_report_id", "report_id"),
        Index("ix_report_chunks_report_id_chunk_index", "report_id", "chunk_index"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(Text())
    chunk_text: Mapped[str] = mapped_column(Text(), nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(20), nullable=False, default="paragraph")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"
    __table_args__ = (
        CheckConstraint("length(quote) > 0", name="ck_evidence_spans_quote_non_empty"),
        CheckConstraint("char_start >= 0", name="ck_evidence_spans_char_start_gte_0"),
        CheckConstraint("char_end >= char_start", name="ck_evidence_spans_char_end_gte_char_start"),
        CheckConstraint(
            "length(supports_claim) > 0", name="ck_evidence_spans_supports_claim_non_empty"
        ),
        CheckConstraint(
            "confidence >= 0 and confidence <= 1",
            name="ck_evidence_spans_confidence_between_0_and_1",
        ),
        Index("ix_evidence_spans_report_id", "report_id"),
        Index("ix_evidence_spans_chunk_id", "chunk_id"),
        Index("ix_evidence_spans_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("report_chunks.id"), nullable=False)
    quote: Mapped[str] = mapped_column(Text(), nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    supports_claim: Mapped[str] = mapped_column(Text(), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_by_agent: Mapped[str] = mapped_column(Text(), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class ExtractedIOC(Base):
    __tablename__ = "extracted_iocs"
    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "ioc_type",
            "normalized_value",
            name="uq_extracted_iocs_report_type_normalized",
        ),
        CheckConstraint(
            "ioc_type in ('ip', 'domain', 'hash', 'url', 'email', 'file_path')",
            name="ck_extracted_iocs_ioc_type_allowed",
        ),
        CheckConstraint(
            "confidence >= 0 and confidence <= 1",
            name="ck_extracted_iocs_confidence_between_0_and_1",
        ),
        Index("ix_extracted_iocs_report_id", "report_id"),
        Index("ix_extracted_iocs_ioc_type", "ioc_type"),
        Index("ix_extracted_iocs_normalized_value", "normalized_value"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_spans.id"))
    ioc_type: Mapped[str] = mapped_column(Text(), nullable=False)
    raw_value: Mapped[str] = mapped_column(Text(), nullable=False)
    normalized_value: Mapped[str] = mapped_column(Text(), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    extractor: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class GraphNode(Base):
    __tablename__ = "graph_nodes"
    __table_args__ = (
        CheckConstraint(GRAPH_NODE_TYPE_CHECK, name="ck_graph_nodes_node_type_allowed"),
        UniqueConstraint("run_id", "node_type", "ref_table", "ref_id", name="uq_graph_nodes_run_type_ref"),
        UniqueConstraint("id", "run_id", name="uq_graph_nodes_id_run"),
        Index("ix_graph_nodes_run_id", "run_id"),
        Index("ix_graph_nodes_node_type", "node_type"),
        Index("ix_graph_nodes_ref_lookup", "ref_table", "ref_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ref_table: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    ref_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class GraphEdge(Base):
    __tablename__ = "graph_edges"
    __table_args__ = (
        CheckConstraint("source_node_id != target_node_id", name="ck_graph_edges_no_self_edge"),
        CheckConstraint(GRAPH_EDGE_TYPE_CHECK, name="ck_graph_edges_edge_type_allowed"),
        UniqueConstraint(
            "run_id",
            "source_node_id",
            "target_node_id",
            "edge_type",
            name="uq_graph_edges_run_source_target_type",
        ),
        ForeignKeyConstraint(
            ["source_node_id", "run_id"],
            ["graph_nodes.id", "graph_nodes.run_id"],
            name="fk_graph_edges_source_node_id_run_graph_nodes",
        ),
        ForeignKeyConstraint(
            ["target_node_id", "run_id"],
            ["graph_nodes.id", "graph_nodes.run_id"],
            name="fk_graph_edges_target_node_id_run_graph_nodes",
        ),
        Index("ix_graph_edges_run_id", "run_id"),
        Index("ix_graph_edges_edge_type", "edge_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class QueryCandidate(Base):
    __tablename__ = "query_candidates"
    __table_args__ = (
        UniqueConstraint("detection_spec_id", "query_id", name="uq_query_candidates_spec_query_id"),
        CheckConstraint(
            "query_type in ('high_precision', 'high_recall', 'balanced')",
            name="ck_query_candidates_query_type_allowed",
        ),
        CheckConstraint(
            "query_language in ('kql', 'spl', 'eql')",
            name="ck_query_candidates_query_language_allowed",
        ),
        Index("ix_query_candidates_detection_spec_id", "detection_spec_id"),
        Index("ix_query_candidates_selected", "selected"),
        Index("ix_query_candidates_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_spec_id: Mapped[str] = mapped_column(ForeignKey("detection_specs.id"), nullable=False)
    query_id: Mapped[str] = mapped_column(Text(), nullable=False)
    query_type: Mapped[str] = mapped_column(Text(), nullable=False)
    query_language: Mapped[str] = mapped_column(Text(), nullable=False)
    query_text: Mapped[str] = mapped_column(Text(), nullable=False)
    expected_signal: Mapped[str] = mapped_column(Text(), nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class AttackMapping(Base):
    __tablename__ = "attack_mappings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_spans.id"), nullable=False)


class TelemetrySelection(Base):
    __tablename__ = "telemetry_selections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    attack_mapping_id: Mapped[str] = mapped_column(ForeignKey("attack_mappings.id"), nullable=False)


class DetectionSpec(Base):
    __tablename__ = "detection_specs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    abstain_code: Mapped[str | None] = mapped_column(String(80))
    abstain_context: Mapped[str | None] = mapped_column(Text())
    abstain_human_message: Mapped[str | None] = mapped_column(Text())
    spec_payload: Mapped[str | None] = mapped_column(Text())
    is_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class GeneratedRule(Base):
    __tablename__ = "generated_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_spec_id: Mapped[str] = mapped_column(ForeignKey("detection_specs.id"), nullable=False)
    query_candidate_id: Mapped[str | None] = mapped_column(ForeignKey("query_candidates.id"))
    rule_content: Mapped[str | None] = mapped_column(Text())
    generation_source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual_draft")
    detection_ast_id: Mapped[str | None] = mapped_column(String(36))
    compiled_sigma_id: Mapped[str | None] = mapped_column(String(36))


class ValidationResult(Base):
    __tablename__ = "validation_results"
    __table_args__ = (
        Index("ix_validation_results_rule_id", "rule_id"),
        Index("ix_validation_results_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    details_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class TestRun(Base):
    __tablename__ = "test_runs"
    __table_args__ = (
        Index("ix_test_runs_rule_id", "rule_id"),
        Index("ix_test_runs_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    result_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint("tokens_in >= 0", name="ck_agent_runs_tokens_in_non_negative"),
        CheckConstraint("tokens_out >= 0", name="ck_agent_runs_tokens_out_non_negative"),
        CheckConstraint("latency_ms >= 0", name="ck_agent_runs_latency_ms_non_negative"),
        CheckConstraint("cost_usd >= 0", name="ck_agent_runs_cost_usd_non_negative"),
        CheckConstraint("retry_attempt >= 0", name="ck_agent_runs_retry_attempt_non_negative"),
        Index("ix_agent_runs_run_id", "run_id"),
        Index("ix_agent_runs_trace_id", "trace_id"),
        Index("ix_agent_runs_agent_name", "agent_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_name: Mapped[str] = mapped_column(Text(), nullable=False)
    input_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    output_hash: Mapped[str | None] = mapped_column(Text())
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    model_id: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    input_payload_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    output_payload_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    artifact_ids_json: Mapped[str] = mapped_column(Text(), nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    retry_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False)


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    __table_args__ = (
        Index("ix_review_decisions_rule_id", "rule_id"),
        Index("ix_review_decisions_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewer: Mapped[str] = mapped_column(Text(), nullable=False)
    comments: Mapped[str] = mapped_column(Text(), nullable=False, default="")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class PipelineRunRecord(Base):
    __tablename__ = "pipeline_runs"
    __table_args__ = (
        Index("ix_pipeline_runs_run_id", "run_id"),
        Index("ix_pipeline_runs_report_id", "report_id"),
        Index("ix_pipeline_runs_detection_spec_id", "detection_spec_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    report_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    detection_spec_id: Mapped[str | None] = mapped_column(String(36))
    rule_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class RetrievalAuditRun(Base):
    __tablename__ = "retrieval_audit_runs"
    __table_args__ = (
        CheckConstraint("length(query_hash) > 0", name="ck_retrieval_audit_runs_query_hash_non_empty"),
        CheckConstraint("top_k > 0", name="ck_retrieval_audit_runs_top_k_positive"),
        Index("ix_retrieval_audit_runs_run_id", "run_id"),
        Index("ix_retrieval_audit_runs_report_id", "report_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text(), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class RetrievalCandidate(Base):
    __tablename__ = "retrieval_candidates"
    __table_args__ = (
        CheckConstraint("rank > 0", name="ck_retrieval_candidates_rank_positive"),
        CheckConstraint("score_sparse >= 0", name="ck_retrieval_candidates_score_sparse_non_negative"),
        CheckConstraint("score_dense >= 0", name="ck_retrieval_candidates_score_dense_non_negative"),
        CheckConstraint("score_fused >= 0", name="ck_retrieval_candidates_score_fused_non_negative"),
        UniqueConstraint("retrieval_run_id", "chunk_id", name="uq_retrieval_candidates_run_chunk"),
        Index("ix_retrieval_candidates_retrieval_run_id", "retrieval_run_id"),
        Index("ix_retrieval_candidates_run_id", "run_id"),
        Index("ix_retrieval_candidates_report_id", "report_id"),
        Index("ix_retrieval_candidates_chunk_id", "chunk_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    retrieval_run_id: Mapped[str] = mapped_column(
        ForeignKey("retrieval_audit_runs.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("report_chunks.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score_sparse: Mapped[float] = mapped_column(Float, nullable=False)
    score_dense: Mapped[float] = mapped_column(Float, nullable=False)
    score_fused: Mapped[float] = mapped_column(Float, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class ProofObligationRecord(Base):
    __tablename__ = "proof_obligations"
    __table_args__ = (
        Index("ix_proof_obligations_rule_candidate_id", "rule_candidate_id"),
        Index("ix_proof_obligations_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    rule_candidate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text(), nullable=False)
    required_artifact_types: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    justification: Mapped[str | None] = mapped_column(Text())


class RefinementIteration(Base):
    __tablename__ = "refinement_iterations"
    __table_args__ = (
        Index("ix_refinement_iterations_detection_spec_id", "detection_spec_id"),
        Index("ix_refinement_iterations_rule_id", "rule_id"),
        Index("ix_refinement_iterations_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_spec_id: Mapped[str | None] = mapped_column(ForeignKey("detection_specs.id"))
    rule_id: Mapped[str | None] = mapped_column(ForeignKey("generated_rules.id"))
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    feedback_ref: Mapped[str] = mapped_column(Text(), nullable=False, default="")
    regression_ref: Mapped[str] = mapped_column(Text(), nullable=False, default="")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class CandidateScore(Base):
    __tablename__ = "candidate_scores"
    __table_args__ = (
        CheckConstraint(
            "score_value >= 0 and score_value <= 1",
            name="ck_candidate_scores_score_value_between_0_and_1",
        ),
        CheckConstraint("length(score_type) > 0", name="ck_candidate_scores_score_type_non_empty"),
        Index("ix_candidate_scores_rule_id", "rule_id"),
        Index("ix_candidate_scores_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.run_id"), nullable=False)
    score_type: Mapped[str] = mapped_column(String(64), nullable=False)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    score_breakdown_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class OracleEvaluationResult(Base):
    __tablename__ = "oracle_evaluation_results"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 and score <= 1",
            name="ck_oracle_evaluation_results_score_between_0_and_1",
        ),
        CheckConstraint(
            "length(oracle_case_id) > 0",
            name="ck_oracle_evaluation_results_oracle_case_id_non_empty",
        ),
        Index("ix_oracle_evaluation_results_rule_id", "rule_id"),
        Index("ix_oracle_evaluation_results_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.run_id"), nullable=False)
    oracle_case_id: Mapped[str] = mapped_column(String(80), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    details_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class RegressionRun(Base):
    __tablename__ = "regression_runs"
    __table_args__ = (
        CheckConstraint(
            "status in ('passed', 'failed', 'unknown')",
            name="ck_regression_runs_status_allowed",
        ),
        Index("ix_regression_runs_rule_id", "rule_id"),
        Index("ix_regression_runs_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.run_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    result_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class QualitySnapshot(Base):
    __tablename__ = "quality_snapshots"
    __table_args__ = (
        CheckConstraint(
            "length(snapshot_type) > 0",
            name="ck_quality_snapshots_snapshot_type_non_empty",
        ),
        Index("ix_quality_snapshots_run_id", "run_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.run_id"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text(), nullable=False, default="{}")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class MemoryView(Base):
    __tablename__ = "memory_views"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(Text(), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
