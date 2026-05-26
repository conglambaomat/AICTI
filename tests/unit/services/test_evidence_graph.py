import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.services.evidence_graph import EvidenceGraphError, EvidenceGraphService


def _empty_db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_missing_required_graph_path_blocks_export() -> None:
    service = EvidenceGraphService(db=None)

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


def test_empty_db_backed_export_path_fails_closed() -> None:
    service = EvidenceGraphService(db=_empty_db_session())

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


def _add_export_path(
    service: EvidenceGraphService,
    *,
    run_id: str = "run-1",
    rule_id: str = "rule-1",
    report_run_id: str | None = None,
    quote_run_id: str | None = None,
    spec_run_id: str | None = None,
    omit_node_type: str | None = None,
    wrong_edge: str | None = None,
) -> None:
    report_node = None
    if omit_node_type != "report":
        report_node = service.upsert_node(
            run_id=report_run_id or run_id,
            node_type="report",
            ref_table="reports",
            ref_id="report-1",
        )
    quote_node = None
    if omit_node_type != "evidence_quote":
        quote_node = service.upsert_node(
            run_id=quote_run_id or run_id,
            node_type="evidence_quote",
            ref_table="evidence_quotes",
            ref_id="quote-1",
        )
    spec_node = None
    if omit_node_type != "detection_spec":
        spec_node = service.upsert_node(
            run_id=spec_run_id or run_id,
            node_type="detection_spec",
            ref_table="detection_specs",
            ref_id="spec-1",
        )
    rule_node = service.upsert_node(
        run_id=run_id,
        node_type="generated_rule",
        ref_table="generated_rules",
        ref_id=rule_id,
    )
    validation_node = None
    if omit_node_type != "validation_result":
        validation_node = service.upsert_node(
            run_id=run_id,
            node_type="validation_result",
            ref_table="validation_results",
            ref_id="validation-1",
        )
    if omit_node_type != "review_decision":
        review_node = service.upsert_node(
            run_id=run_id,
            node_type="review_decision",
            ref_table="review_decisions",
            ref_id="review-1",
        )
        service.add_edge(
            run_id=run_id,
            source_node_id=rule_node,
            target_node_id=review_node,
            edge_type="satisfies" if wrong_edge == "review_decision" else "validated_by",
        )
    if omit_node_type != "proof_obligation" and validation_node is not None:
        proof_node = service.upsert_node(
            run_id=run_id,
            node_type="proof_obligation",
            ref_table="proof_obligations",
            ref_id="proof-1",
        )
        service.add_edge(
            run_id=run_id,
            source_node_id=validation_node,
            target_node_id=proof_node,
            edge_type="derived_from" if wrong_edge == "proof_obligation" else "satisfies",
        )
    if (
        report_node is not None
        and quote_node is not None
        and (report_run_id is None or report_run_id == run_id)
        and (quote_run_id is None or quote_run_id == run_id)
    ):
        service.add_edge(
            run_id=run_id,
            source_node_id=report_node,
            target_node_id=quote_node,
            edge_type="supports" if wrong_edge == "evidence_quote" else "derived_from",
        )
    if (
        quote_node is not None
        and spec_node is not None
        and (quote_run_id is None or quote_run_id == run_id)
        and (spec_run_id is None or spec_run_id == run_id)
    ):
        service.add_edge(
            run_id=run_id,
            source_node_id=quote_node,
            target_node_id=spec_node,
            edge_type="derived_from" if wrong_edge == "detection_spec" else "supports",
        )
    if spec_node is not None and (spec_run_id is None or spec_run_id == run_id):
        service.add_edge(
            run_id=run_id,
            source_node_id=spec_node,
            target_node_id=rule_node,
            edge_type="derived_from",
        )
    if validation_node is not None:
        service.add_edge(
            run_id=run_id,
            source_node_id=rule_node,
            target_node_id=validation_node,
            edge_type="validated_by",
        )


def test_complete_same_run_graph_path_passes() -> None:
    session = _empty_db_session()
    service = EvidenceGraphService(db=session)
    _add_export_path(service)
    session.commit()

    service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


def test_missing_review_decision_fails_export_path() -> None:
    session = _empty_db_session()
    service = EvidenceGraphService(db=session)
    _add_export_path(service, omit_node_type="review_decision")
    session.commit()

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


@pytest.mark.parametrize(
    "missing_node_type", ["report", "evidence_quote", "validation_result", "proof_obligation"]
)
def test_missing_report_quote_validation_or_proof_fails_export_path(
    missing_node_type: str,
) -> None:
    session = _empty_db_session()
    service = EvidenceGraphService(db=session)
    _add_export_path(service, omit_node_type=missing_node_type)
    session.commit()

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


@pytest.mark.parametrize(
    ("cross_run_node", "kwargs"),
    [
        ("report", {"report_run_id": "other-run"}),
        ("evidence_quote", {"quote_run_id": "other-run"}),
        ("detection_spec", {"spec_run_id": "other-run"}),
    ],
)
def test_cross_run_upstream_lineage_cannot_satisfy_export_path(
    cross_run_node: str,
    kwargs: dict[str, str],
) -> None:
    session = _empty_db_session()
    service = EvidenceGraphService(db=session)
    _add_export_path(service, **kwargs)
    session.commit()

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


@pytest.mark.parametrize(
    "wrong_edge",
    [
        "evidence_quote",
        "detection_spec",
        "review_decision",
        "proof_obligation",
    ],
)
def test_wrong_edge_type_in_export_path_fails(wrong_edge: str) -> None:
    session = _empty_db_session()
    service = EvidenceGraphService(db=session)
    _add_export_path(service, wrong_edge=wrong_edge)
    session.commit()

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")
