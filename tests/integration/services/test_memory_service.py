"""Integration tests for memory policy and memory-service integrity behavior."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.services.memory_policy import MemoryPolicyEngine
from de_forge.services.memory_service import MemoryService, MemoryVersionConflictError


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


def test_policy_default_deny_unknown_role() -> None:
    policy = MemoryPolicyEngine()

    allowed = policy.can_access(
        role="unknown_role",
        namespace="evidence.working_set",
        operation="read",
        stage="evidence",
        run_state="ingested",
    )

    assert allowed is False


def test_policy_allows_whitelisted_role_namespace_operation() -> None:
    policy = MemoryPolicyEngine()

    allowed = policy.can_access(
        role="attack_mapping_agent",
        namespace="evidence.working_set",
        operation="read",
        stage="attack_mapping",
        run_state="evidence_ready",
    )

    assert allowed is True


def test_write_rejects_stale_expected_version() -> None:
    db = _build_session()
    service = MemoryService(db)

    first = service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a"]},
        expected_version=0,
    )
    assert first.version == 1

    with pytest.raises(MemoryVersionConflictError):
        service.write(
            run_id="run-1",
            namespace="evidence.working_set",
            role="evidence_agent",
            stage="evidence",
            operation="write",
            payload={"spans": ["b"]},
            expected_version=0,
        )


def test_write_links_prev_hash_to_new_event_hash() -> None:
    db = _build_session()
    service = MemoryService(db)

    first = service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a"]},
        expected_version=0,
    )
    second = service.write(
        run_id="run-1",
        namespace="evidence.working_set",
        role="evidence_agent",
        stage="evidence",
        operation="write",
        payload={"spans": ["a", "b"]},
        expected_version=1,
    )

    event2_value = db.execute(
        text("SELECT value FROM memory_events WHERE scope = :scope AND key = '2'"),
        {"scope": "run-1:evidence.working_set"},
    ).scalar_one()
    event2_payload = json.loads(event2_value)
    assert event2_payload["prev_hash"] == first.event_hash
    assert event2_payload["event_hash"] == second.event_hash

    view_value = db.execute(
        text("SELECT value FROM memory_views WHERE scope = :scope AND key = 'latest'"),
        {"scope": "run-1:evidence.working_set"},
    ).scalar_one()
    view_payload = json.loads(view_value)
    assert view_payload["version"] == 2
    assert view_payload["last_event_hash"] == second.event_hash
