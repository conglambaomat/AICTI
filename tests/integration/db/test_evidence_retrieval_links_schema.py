from typing import Any

import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing_extensions import Protocol

import de_forge.models  # noqa: F401
from de_forge.db.base import Base
from de_forge.models.contract import EvidenceRetrievalLink


class _SQLiteConnection(Protocol):
    def execute(self, statement: str, parameters: Any = ...) -> Any: ...


def create_sqlite_engine_with_foreign_keys() -> Engine:
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: _SQLiteConnection, _connection_record: object) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine


def test_evidence_retrieval_links_table_exists_with_required_constraints() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    assert "evidence_retrieval_links" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("evidence_retrieval_links")}
    assert {"id", "run_id", "evidence_id", "retrieval_candidate_id", "created_at"}.issubset(columns)

    foreign_keys = {
        foreign_key["name"]: (
            tuple(foreign_key["constrained_columns"]),
            foreign_key["referred_table"],
            tuple(foreign_key["referred_columns"]),
        )
        for foreign_key in inspector.get_foreign_keys("evidence_retrieval_links")
    }
    assert foreign_keys["fk_evidence_retrieval_links_evidence_id_evidence_spans"] == (
        ("evidence_id",),
        "evidence_spans",
        ("id",),
    )
    assert foreign_keys[
        "fk_evidence_retrieval_links_retrieval_candidate_id_retrieval_candidates"
    ] == (
        ("retrieval_candidate_id",),
        "retrieval_candidates",
        ("id",),
    )

    unique_constraints = {
        constraint["name"]: tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("evidence_retrieval_links")
    }
    assert unique_constraints["uq_evidence_retrieval_links_run_evidence_candidate"] == (
        "run_id",
        "evidence_id",
        "retrieval_candidate_id",
    )


def test_missing_evidence_retrieval_link_evidence_is_rejected() -> None:
    engine = create_sqlite_engine_with_foreign_keys()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        session.add(
            EvidenceRetrievalLink(
                id="link-1",
                run_id="run-1",
                evidence_id="missing-evidence",
                retrieval_candidate_id="missing-candidate",
                created_at="2026-05-27T00:00:00Z",
            )
        )

        with pytest.raises(IntegrityError):
            session.commit()
