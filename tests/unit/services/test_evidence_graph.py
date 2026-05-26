import pytest

from de_forge.services.evidence_graph import EvidenceGraphError, EvidenceGraphService


def test_missing_required_graph_path_blocks_export() -> None:
    service = EvidenceGraphService(db=None)

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")


def test_db_backed_export_path_fails_closed_until_traversal_is_implemented() -> None:
    service = EvidenceGraphService(db=object())  # type: ignore[arg-type]

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")
