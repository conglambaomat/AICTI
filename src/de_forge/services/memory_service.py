"""Memory service with versioned writes and hash-chain integrity."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from de_forge.core.hashing import snapshot_hash


class MemoryPolicyEngine:
    """Fail-closed policy engine for memory operations."""

    def can_access(
        self,
        *,
        role: str,
        namespace: str,
        operation: str,
        stage: str,
        run_state: str,
    ) -> bool:
        return bool(role and namespace and operation == "write" and stage and run_state == "active")


class MemoryAccessDeniedError(RuntimeError):
    """Raised when memory policy rejects access."""


class MemoryVersionConflictError(RuntimeError):
    """Raised when expected version does not match current version."""


class MemoryWriteResult:
    def __init__(self, *, version: int, event_hash: str) -> None:
        self.version = version
        self.event_hash = event_hash


class MemoryService:
    def __init__(self, db: Session, policy: MemoryPolicyEngine | None = None) -> None:
        self.db = db
        self.policy = policy or MemoryPolicyEngine()

    def write(
        self,
        *,
        run_id: str,
        namespace: str,
        role: str,
        stage: str,
        operation: str,
        payload: dict[str, object],
        expected_version: int,
    ) -> MemoryWriteResult:
        if not self.policy.can_access(
            role=role,
            namespace=namespace,
            operation=operation,
            stage=stage,
            run_state="active",
        ):
            raise MemoryAccessDeniedError("memory access denied")

        scope = f"{run_id}:{namespace}"
        view_row = self.db.execute(
            text("SELECT value FROM memory_views WHERE scope = :scope AND key = 'latest'"),
            {"scope": scope},
        ).fetchone()

        current_version = 0
        prev_hash: str | None = None
        if view_row is not None:
            state = json.loads(view_row[0])
            current_version = int(state["version"])
            prev_hash = str(state["last_event_hash"])

        if expected_version != current_version:
            raise MemoryVersionConflictError("expected_version mismatch")

        new_version = current_version + 1
        event_hash = snapshot_hash(
            {
                "run_id": run_id,
                "namespace": namespace,
                "version": new_version,
                "payload": payload,
                "prev_hash": prev_hash,
                "actor_role": role,
                "stage": stage,
            }
        )

        timestamp = datetime.now(UTC).isoformat()
        event_payload = {
            "run_id": run_id,
            "namespace": namespace,
            "version": new_version,
            "payload": payload,
            "prev_hash": prev_hash,
            "event_hash": event_hash,
            "actor_role": role,
            "stage": stage,
        }
        self.db.execute(
            text(
                """
                INSERT INTO memory_events (id, scope, key, value, created_at)
                VALUES (:id, :scope, :key, :value, :created_at)
                """
            ),
            {
                "id": str(uuid4()),
                "scope": scope,
                "key": str(new_version),
                "value": json.dumps(event_payload, sort_keys=True),
                "created_at": timestamp,
            },
        )

        new_view_payload = {
            "version": new_version,
            "payload": payload,
            "last_event_hash": event_hash,
        }
        self.db.execute(
            text(
                """
                INSERT INTO memory_views (id, scope, key, value, updated_at)
                VALUES (:id, :scope, 'latest', :value, :updated_at)
                ON CONFLICT(scope, key)
                DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """
            ),
            {
                "id": str(uuid4()),
                "scope": scope,
                "value": json.dumps(new_view_payload, sort_keys=True),
                "updated_at": timestamp,
            },
        )

        self.db.commit()
        return MemoryWriteResult(version=new_version, event_hash=event_hash)
