"""Core persistence contract models."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


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
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(Text())
    chunk_text: Mapped[str] = mapped_column(Text(), nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(20), nullable=False, default="paragraph")
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("report_chunks.id"), nullable=False, index=True)
    quote: Mapped[str] = mapped_column(Text(), nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    supports_claim: Mapped[str] = mapped_column(Text(), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_by_agent: Mapped[str] = mapped_column(Text(), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
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


class GeneratedRule(Base):
    __tablename__ = "generated_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_spec_id: Mapped[str] = mapped_column(ForeignKey("detection_specs.id"), nullable=False)


class ValidationResult(Base):
    __tablename__ = "validation_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)


class TestRun(Base):
    __tablename__ = "test_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    trace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_name: Mapped[str] = mapped_column(Text(), nullable=False)
    input_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    output_hash: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    retry_attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[str] = mapped_column(String(40), nullable=False)


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("generated_rules.id"), nullable=False)


class RefinementIteration(Base):
    __tablename__ = "refinement_iterations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detection_spec_id: Mapped[str | None] = mapped_column(ForeignKey("detection_specs.id"))
    rule_id: Mapped[str | None] = mapped_column(ForeignKey("generated_rules.id"))
