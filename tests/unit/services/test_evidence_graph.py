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
