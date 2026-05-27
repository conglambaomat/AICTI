from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.services.memory_service import MemoryIntegrityError, MemoryService


def _build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE memory_events (
                    id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE memory_views (
                    id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(scope, key)
                )
                """
            )
        )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def test_replay_reconstructs_materialized_view_hash() -> None:
    db = _build_session()
    service = MemoryService(db)

    service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a"]},
        expected_version=0,
    )
    service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a", "b"]},
        expected_version=1,
    )

    report = service.replay(run_id="run-1")
    assert report["integrity_ok"] is True


def test_replay_fails_when_event_payload_tampered() -> None:
    db = _build_session()
    service = MemoryService(db)

    service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a"]},
        expected_version=0,
    )

    row = db.execute(
        text("SELECT id, value FROM memory_events WHERE scope = :scope AND key = '1'"),
        {"scope": "run-1:evidence.working_set"},
    ).fetchone()
    assert row is not None
    payload = json.loads(row[1])
    payload["payload"] = {"tampered": True}
    db.execute(
        text("UPDATE memory_events SET value = :value WHERE id = :id"),
        {"id": row[0], "value": json.dumps(payload, sort_keys=True)},
    )
    db.commit()

    with pytest.raises(MemoryIntegrityError):
        service.replay(run_id="run-1")
