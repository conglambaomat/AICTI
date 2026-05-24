"""Retrieval audit lineage persistence service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from de_forge.models import RetrievalAuditRun, RetrievalCandidate
from de_forge.services.retrieval import ScoredChunk


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class RetrievalAuditService:
    """Persist retrieval audit runs and their ranked candidates."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_retrieval(
        self,
        *,
        run_id: str,
        report_id: str,
        query_text: str,
        retrieval_mode: str,
        top_k: int,
        candidates: list[ScoredChunk],
    ) -> RetrievalAuditRun:
        created_at = _utc_now_iso()
        audit_run = RetrievalAuditRun(
            id=str(uuid.uuid4()),
            run_id=run_id,
            report_id=report_id,
            query_text=query_text,
            query_hash=hashlib.sha256(query_text.encode("utf-8")).hexdigest(),
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            created_at=created_at,
        )
        self.db.add(audit_run)

        for rank, candidate in enumerate(candidates, start=1):
            self.db.add(
                RetrievalCandidate(
                    id=str(uuid.uuid4()),
                    retrieval_run_id=audit_run.id,
                    run_id=run_id,
                    report_id=report_id,
                    chunk_id=candidate.chunk_id,
                    rank=rank,
                    score_sparse=candidate.score_sparse,
                    score_dense=candidate.score_dense,
                    score_fused=candidate.score_fused,
                    selected=rank <= top_k,
                    created_at=created_at,
                )
            )

        self.db.commit()
        self.db.refresh(audit_run)
        return audit_run
