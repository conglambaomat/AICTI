"""Integration tests for evidence extraction service."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import EvidenceSpan, Report, ReportChunk
from de_forge.models.evidence_graph import EvidenceEdge, EvidenceNode
from de_forge.services.evidence import EvidenceExtractionError, EvidenceInput, EvidenceService
from de_forge.services.evidence_graph import EvidenceGraphStore


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_and_chunk(
    db: Session,
    chunk_text: str = "powershell -enc abc",
    chunk_char_start: int = 0,
) -> tuple[str, str]:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text=chunk_text,
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=created_at,
        updated_at=created_at,
    )
    chunk = ReportChunk(
        id="chunk-1",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text=chunk_text,
        char_start=chunk_char_start,
        char_end=chunk_char_start + len(chunk_text),
        chunk_type="paragraph",
        created_at=created_at,
    )
    db.add(report)
    db.add(chunk)
    db.commit()
    return report.id, chunk.id


def test_empty_evidence_payload_transitions_to_failed_generation() -> None:
    """Empty evidence payload must fail-fast and persist nothing."""
    db = _build_session()
    report_id, _ = _seed_report_and_chunk(db)
    service = EvidenceService(db)

    with pytest.raises(EvidenceExtractionError, match="evidence"):
        service.persist_evidence(
            report_id=report_id, run_id="run-1", created_by_agent="evidence-agent", evidence=[]
        )

    persisted = (
        db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    )
    assert persisted == []


def test_valid_evidence_persists_with_lineage_fields() -> None:
    """Valid evidence should persist with report_id, chunk_id, and evidence_id lineage."""
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(db)
    service = EvidenceService(db)

    result = service.persist_evidence(
        report_id=report_id,
        run_id="run-2",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-1",
                chunk_id=chunk_id,
                quote="powershell -enc abc",
                char_start=0,
                char_end=19,
                supports_claim="Encoded PowerShell command execution observed",
                confidence=0.92,
            )
        ],
    )

    assert result == ["evidence-1"]

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.id == "evidence-1")).scalar_one()
    assert persisted.id == "evidence-1"
    assert persisted.report_id == report_id
    assert persisted.chunk_id == chunk_id
    assert persisted.run_id == "run-2"

    evidence_created = datetime.fromisoformat(persisted.created_at.replace("Z", "+00:00"))
    assert evidence_created.year >= 2025
    assert evidence_created.tzinfo == UTC
    assert persisted.created_at != "1970-01-01T00:00:00Z"

    report = db.get(Report, report_id)
    assert report is not None
    report_created = datetime.fromisoformat(report.created_at.replace("Z", "+00:00"))
    report_updated = datetime.fromisoformat(report.updated_at.replace("Z", "+00:00"))
    assert report_created.year >= 2025
    assert report_updated.year >= 2025
    assert report_created.tzinfo == UTC
    assert report_updated.tzinfo == UTC
    assert report.created_at != "1970-01-01T00:00:00Z"
    assert report.updated_at != "1970-01-01T00:00:00Z"

    chunk = db.get(ReportChunk, chunk_id)
    assert chunk is not None
    chunk_created = datetime.fromisoformat(chunk.created_at.replace("Z", "+00:00"))
    assert chunk_created.year >= 2025
    assert chunk_created.tzinfo == UTC
    assert chunk.created_at != "1970-01-01T00:00:00Z"


def test_evidence_with_nonzero_chunk_start_validates_absolute_offsets() -> None:
    """Evidence offsets are absolute and must stay within non-zero chunk bounds."""
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(db, chunk_char_start=100)
    service = EvidenceService(db)

    result = service.persist_evidence(
        report_id=report_id,
        run_id="run-3",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-2",
                chunk_id=chunk_id,
                quote="powershell -enc",
                char_start=100,
                char_end=115,
                supports_claim="PowerShell execution detected",
                confidence=0.88,
            )
        ],
    )

    assert result == ["evidence-2"]

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.id == "evidence-2")).scalar_one()
    assert persisted.char_start == 100
    assert persisted.char_end == 115
    assert persisted.chunk_id == chunk_id


def test_evidence_quote_must_match_persisted_chunk_text_at_absolute_offsets() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(
        db, chunk_text="attacker launched powershell -enc abc", chunk_char_start=40
    )
    service = EvidenceService(db)

    with pytest.raises(EvidenceExtractionError, match="quote does not match chunk text"):
        service.persist_evidence(
            report_id=report_id,
            run_id="run-mismatch",
            created_by_agent="evidence-agent",
            evidence=[
                EvidenceInput(
                    evidence_id="evidence-mismatch",
                    chunk_id=chunk_id,
                    quote="cmd.exe /c whoami",
                    char_start=58,
                    char_end=73,
                    supports_claim="Encoded PowerShell execution observed",
                    confidence=0.91,
                )
            ],
        )

    persisted = (
        db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    )
    assert persisted == []


def test_evidence_graph_rejects_unknown_node_type() -> None:
    db = _build_session()
    graph = EvidenceGraphStore(db)

    with pytest.raises(ValueError, match="unsupported node_type"):
        graph.add_node(run_id="run-lineage-1", node_type="random", payload={"id": "x"})


def test_evidence_graph_rejects_unknown_edge_type() -> None:
    db = _build_session()
    graph = EvidenceGraphStore(db)

    quote_node = graph.add_node(
        run_id="run-lineage-2", node_type="evidence_quote", payload={"evidence_id": "ev-1"}
    )
    strategy_node = graph.add_node(
        run_id="run-lineage-2",
        node_type="detection_strategy",
        payload={"strategy": "behavioral"},
    )

    with pytest.raises(ValueError, match="unsupported edge_type"):
        graph.add_edge(
            run_id="run-lineage-2",
            source_node_id=quote_node,
            target_node_id=strategy_node,
            edge_type="unknown_link",
        )


def test_evidence_graph_requires_typed_lineage_path_quote_to_reviewed_rule_candidate() -> None:
    db = _build_session()
    graph = EvidenceGraphStore(db)

    quote_node = graph.add_node(
        run_id="run-lineage-3", node_type="evidence_quote", payload={"evidence_id": "ev-2"}
    )
    strategy_node = graph.add_node(
        run_id="run-lineage-3",
        node_type="detection_strategy",
        payload={"strategy": "behavioral"},
    )
    analytic_node = graph.add_node(
        run_id="run-lineage-3", node_type="analytic", payload={"analytic": "powershell suspicious"}
    )
    data_component_node = graph.add_node(
        run_id="run-lineage-3",
        node_type="data_component",
        payload={"component": "process creation"},
    )
    telemetry_node = graph.add_node(
        run_id="run-lineage-3", node_type="telemetry_source", payload={"source": "windows eventlog"}
    )
    rule_candidate_node = graph.add_node(
        run_id="run-lineage-3",
        node_type="reviewed_rule_candidate",
        payload={"rule_id": "rule-1"},
    )

    graph.add_edge(
        run_id="run-lineage-3",
        source_node_id=quote_node,
        target_node_id=strategy_node,
        edge_type="supports",
    )
    graph.add_edge(
        run_id="run-lineage-3",
        source_node_id=strategy_node,
        target_node_id=analytic_node,
        edge_type="derives",
    )
    graph.add_edge(
        run_id="run-lineage-3",
        source_node_id=analytic_node,
        target_node_id=data_component_node,
        edge_type="maps_to",
    )
    graph.add_edge(
        run_id="run-lineage-3",
        source_node_id=data_component_node,
        target_node_id=telemetry_node,
        edge_type="maps_to",
    )
    graph.add_edge(
        run_id="run-lineage-3",
        source_node_id=telemetry_node,
        target_node_id=rule_candidate_node,
        edge_type="implements",
    )

    assert (
        graph.has_required_lineage_path(
            run_id="run-lineage-3",
            from_node_type="evidence_quote",
            to_node_type="reviewed_rule_candidate",
        )
        is True
    )


def test_evidence_graph_reports_missing_required_typed_lineage_path() -> None:
    db = _build_session()
    graph = EvidenceGraphStore(db)

    quote_node = graph.add_node(
        run_id="run-lineage-4", node_type="evidence_quote", payload={"evidence_id": "ev-3"}
    )
    strategy_node = graph.add_node(
        run_id="run-lineage-4",
        node_type="detection_strategy",
        payload={"strategy": "behavioral"},
    )
    reviewed_node = graph.add_node(
        run_id="run-lineage-4",
        node_type="reviewed_rule_candidate",
        payload={"rule_id": "rule-2"},
    )

    graph.add_edge(
        run_id="run-lineage-4",
        source_node_id=quote_node,
        target_node_id=strategy_node,
        edge_type="supports",
    )
    graph.add_edge(
        run_id="run-lineage-4",
        source_node_id=strategy_node,
        target_node_id=reviewed_node,
        edge_type="supports",
    )

    assert (
        graph.has_required_lineage_path(
            run_id="run-lineage-4",
            from_node_type="evidence_quote",
            to_node_type="reviewed_rule_candidate",
        )
        is False
    )

    persisted_nodes = (
        db.execute(select(EvidenceNode).where(EvidenceNode.run_id == "run-lineage-4"))
        .scalars()
        .all()
    )
    persisted_edges = (
        db.execute(select(EvidenceEdge).where(EvidenceEdge.run_id == "run-lineage-4"))
        .scalars()
        .all()
    )
    assert len(persisted_nodes) == 3
    assert len(persisted_edges) == 2
