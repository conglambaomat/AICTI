"""Agent audit service with snapshot hash verification."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.core.hashing import snapshot_hash, verify_snapshot_hash
from de_forge.models import AgentRun as AgentRunModel
from de_forge.schemas.agent_io import AgentOutputEnvelope


class IntegrityError(ValueError):
    """Raised when agent run snapshot hash verification fails."""


class AgentAuditService:
    """Service for persisting and verifying agent run audit snapshots."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def persist(
        self, input_payload: dict[str, Any], output_envelope: AgentOutputEnvelope
    ) -> AgentRunModel:
        output_payload = output_envelope.model_dump(mode="json")
        output_hash = snapshot_hash(output_payload)
        record = AgentRunModel(
            id=str(uuid4()),
            run_id=output_envelope.run_id,
            trace_id=output_envelope.run_id,
            agent_name=output_envelope.agent_name,
            input_hash=snapshot_hash(input_payload),
            output_hash=output_hash,
            status="abstain" if output_envelope.abstain else "success",
            retry_attempt=0,
            started_at="2026-05-20T00:00:00Z",
        )
        self.db.add(record)
        self.db.flush()
        return record

    def persist_agent_run(
        self,
        run_id: str,
        trace_id: str,
        agent_name: str,
        input_snapshot: dict[str, Any],
        output_snapshot: dict[str, Any] | None,
        status: str,
        retry_attempt: int = 0,
    ) -> str:
        """Persist agent run with computed input/output hashes."""
        agent_run_id = str(uuid4())
        input_hash = snapshot_hash(input_snapshot)
        output_hash = snapshot_hash(output_snapshot) if output_snapshot is not None else None

        try:
            self.db.add(
                AgentRunModel(
                    id=agent_run_id,
                    run_id=run_id,
                    trace_id=trace_id,
                    agent_name=agent_name,
                    input_hash=input_hash,
                    output_hash=output_hash,
                    status=status,
                    retry_attempt=retry_attempt,
                    started_at="2026-05-20T00:00:00Z",
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return agent_run_id

    def load_agent_run_verified(
        self,
        run_id: str,
        input_snapshot: dict[str, Any],
    ) -> AgentRunModel:
        """Load agent run and verify input snapshot hash integrity."""
        agent_run = self.db.execute(
            select(AgentRunModel).where(AgentRunModel.id == run_id)
        ).scalar_one_or_none()

        if agent_run is None:
            raise ValueError(f"agent run {run_id} not found")

        if not verify_snapshot_hash(input_snapshot, agent_run.input_hash):
            raise IntegrityError(
                "input hash mismatch: stored hash does not match provided snapshot"
            )

        return agent_run
