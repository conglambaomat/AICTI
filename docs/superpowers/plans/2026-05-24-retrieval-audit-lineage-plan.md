# Retrieval Audit Lineage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist retrieval audit lineage and replace placeholder run lineage responses with DB-derived report/chunk/evidence lineage.

**Architecture:** Add first-class retrieval audit tables for retrieval runs and candidate chunks, then introduce a small service that records retrieval results against persisted `ReportChunk` rows. Keep the existing in-memory retrieval ranking algorithm unchanged; this phase only adds persistence/auditability and DB-backed read APIs.

**Tech Stack:** Python 3.11, SQLAlchemy ORM, Alembic, FastAPI, Pydantic v2, SQLite integration tests, pytest.

---

## File Structure

- Modify `src/de_forge/models/contract.py`
  - Add `RetrievalAuditRun` and `RetrievalCandidate` ORM models.
- Create `alembic/versions/20260524_02_retrieval_audit_lineage.py`
  - Add migration tables, indexes, FKs, and check constraints.
- Create `src/de_forge/services/retrieval_audit.py`
  - Persist retrieval audit runs and candidate chunk rows.
  - Query DB-backed run lineage.
- Modify `src/de_forge/api/routes/runs.py`
  - Inject DB session.
  - Replace hardcoded run/evidence/detail endpoints with persisted state for the endpoints covered in this phase.
  - Keep `/runs/golden` unchanged unless tests require import adjustment.
- Modify or create `tests/integration/services/test_retrieval_audit.py`
  - Cover audit persistence and lineage joins.
- Modify or create `tests/integration/api/test_runs_lineage.py`
  - Cover API responses are DB-derived, not placeholders.
- Modify `tests/integration/db/test_migrations_contract.py`
  - Add schema/model parity assertions for retrieval audit tables.

---

### Task 1: Add retrieval audit persistence models and migration

**Files:**
- Modify: `src/de_forge/models/contract.py`
- Create: `alembic/versions/20260524_02_retrieval_audit_lineage.py`
- Modify: `tests/integration/db/test_migrations_contract.py`

- [ ] **Step 1: Write failing schema contract tests**

Add this test near the other model/migration parity assertions in `tests/integration/db/test_migrations_contract.py`:

```python
def test_retrieval_audit_tables_exist_after_migration(migrated_connection) -> None:
    inspector = inspect(migrated_connection)

    assert "retrieval_audit_runs" in inspector.get_table_names()
    assert "retrieval_candidates" in inspector.get_table_names()

    run_columns = {column["name"] for column in inspector.get_columns("retrieval_audit_runs")}
    assert {
        "id",
        "run_id",
        "report_id",
        "query_text",
        "query_hash",
        "retrieval_mode",
        "top_k",
        "created_at",
    }.issubset(run_columns)

    candidate_columns = {column["name"] for column in inspector.get_columns("retrieval_candidates")}
    assert {
        "id",
        "retrieval_run_id",
        "run_id",
        "report_id",
        "chunk_id",
        "rank",
        "score_sparse",
        "score_dense",
        "score_fused",
        "selected",
        "created_at",
    }.issubset(candidate_columns)
```

If the file uses a different migrated connection fixture name, use the existing fixture from that file and keep the assertion body unchanged.

- [ ] **Step 2: Run the failing schema test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py::test_retrieval_audit_tables_exist_after_migration -q
```

Expected: FAIL because `retrieval_audit_runs` and `retrieval_candidates` do not exist.

- [ ] **Step 3: Add ORM models**

Append these classes after `PipelineRunRecord` in `src/de_forge/models/contract.py`:

```python
class RetrievalAuditRun(Base):
    __tablename__ = "retrieval_audit_runs"
    __table_args__ = (
        CheckConstraint("length(query_hash) > 0", name="ck_retrieval_audit_runs_query_hash_non_empty"),
        CheckConstraint("top_k > 0", name="ck_retrieval_audit_runs_top_k_positive"),
        Index("ix_retrieval_audit_runs_run_id", "run_id"),
        Index("ix_retrieval_audit_runs_report_id", "report_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text(), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieval_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)


class RetrievalCandidate(Base):
    __tablename__ = "retrieval_candidates"
    __table_args__ = (
        CheckConstraint("rank > 0", name="ck_retrieval_candidates_rank_positive"),
        CheckConstraint("score_sparse >= 0", name="ck_retrieval_candidates_score_sparse_non_negative"),
        CheckConstraint("score_dense >= 0", name="ck_retrieval_candidates_score_dense_non_negative"),
        CheckConstraint("score_fused >= 0", name="ck_retrieval_candidates_score_fused_non_negative"),
        UniqueConstraint("retrieval_run_id", "chunk_id", name="uq_retrieval_candidates_run_chunk"),
        Index("ix_retrieval_candidates_retrieval_run_id", "retrieval_run_id"),
        Index("ix_retrieval_candidates_run_id", "run_id"),
        Index("ix_retrieval_candidates_report_id", "report_id"),
        Index("ix_retrieval_candidates_chunk_id", "chunk_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    retrieval_run_id: Mapped[str] = mapped_column(
        ForeignKey("retrieval_audit_runs.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.id"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("report_chunks.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score_sparse: Mapped[float] = mapped_column(Float, nullable=False)
    score_dense: Mapped[float] = mapped_column(Float, nullable=False)
    score_fused: Mapped[float] = mapped_column(Float, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
```

- [ ] **Step 4: Add Alembic migration**

Create `alembic/versions/20260524_02_retrieval_audit_lineage.py` with:

```python
"""Add retrieval audit lineage tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_02"
down_revision = "20260524_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retrieval_audit_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("query_hash", sa.String(length=64), nullable=False),
        sa.Column("retrieval_mode", sa.String(length=40), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint("length(query_hash) > 0", name="ck_retrieval_audit_runs_query_hash_non_empty"),
        sa.CheckConstraint("top_k > 0", name="ck_retrieval_audit_runs_top_k_positive"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_retrieval_audit_runs_run_id", "retrieval_audit_runs", ["run_id"])
    op.create_index("ix_retrieval_audit_runs_report_id", "retrieval_audit_runs", ["report_id"])

    op.create_table(
        "retrieval_candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("retrieval_run_id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=36), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score_sparse", sa.Float(), nullable=False),
        sa.Column("score_dense", sa.Float(), nullable=False),
        sa.Column("score_fused", sa.Float(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.CheckConstraint("rank > 0", name="ck_retrieval_candidates_rank_positive"),
        sa.CheckConstraint("score_sparse >= 0", name="ck_retrieval_candidates_score_sparse_non_negative"),
        sa.CheckConstraint("score_dense >= 0", name="ck_retrieval_candidates_score_dense_non_negative"),
        sa.CheckConstraint("score_fused >= 0", name="ck_retrieval_candidates_score_fused_non_negative"),
        sa.ForeignKeyConstraint(["chunk_id"], ["report_chunks.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["retrieval_audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("retrieval_run_id", "chunk_id", name="uq_retrieval_candidates_run_chunk"),
    )
    op.create_index("ix_retrieval_candidates_retrieval_run_id", "retrieval_candidates", ["retrieval_run_id"])
    op.create_index("ix_retrieval_candidates_run_id", "retrieval_candidates", ["run_id"])
    op.create_index("ix_retrieval_candidates_report_id", "retrieval_candidates", ["report_id"])
    op.create_index("ix_retrieval_candidates_chunk_id", "retrieval_candidates", ["chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_retrieval_candidates_chunk_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_report_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_run_id", table_name="retrieval_candidates")
    op.drop_index("ix_retrieval_candidates_retrieval_run_id", table_name="retrieval_candidates")
    op.drop_table("retrieval_candidates")
    op.drop_index("ix_retrieval_audit_runs_report_id", table_name="retrieval_audit_runs")
    op.drop_index("ix_retrieval_audit_runs_run_id", table_name="retrieval_audit_runs")
    op.drop_table("retrieval_audit_runs")
```

- [ ] **Step 5: Run schema tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py::test_retrieval_audit_tables_exist_after_migration -q
```

Expected: PASS.

- [ ] **Step 6: Run migration/schema contract backstop**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/models/contract.py alembic/versions/20260524_02_retrieval_audit_lineage.py tests/integration/db/test_migrations_contract.py
git commit -m "feat(retrieval): add audit lineage schema

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Persist retrieval audit runs and candidate chunks

**Files:**
- Create: `src/de_forge/services/retrieval_audit.py`
- Create: `tests/integration/services/test_retrieval_audit.py`

- [ ] **Step 1: Write failing persistence tests**

Create `tests/integration/services/test_retrieval_audit.py` with:

```python
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from de_forge.db.base import Base
from de_forge.models import Report, ReportChunk, RetrievalAuditRun, RetrievalCandidate
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return maker()


def _seed_report_with_chunks(db: Session) -> tuple[str, list[str]]:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-1",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text="first behavior second behavior",
        content_hash="hash-1",
        metadata_json="{}",
        status="ingested",
        created_at=created_at,
        updated_at=created_at,
    )
    chunks = [
        ReportChunk(
            id="chunk-1",
            report_id=report.id,
            chunk_index=0,
            section_title=None,
            chunk_text="first behavior",
            char_start=0,
            char_end=14,
            chunk_type="paragraph",
            created_at=created_at,
        ),
        ReportChunk(
            id="chunk-2",
            report_id=report.id,
            chunk_index=1,
            section_title=None,
            chunk_text="second behavior",
            char_start=15,
            char_end=30,
            chunk_type="paragraph",
            created_at=created_at,
        ),
    ]
    db.add(report)
    db.add_all(chunks)
    db.commit()
    return report.id, [chunk.id for chunk in chunks]


def test_record_retrieval_persists_run_and_ranked_candidates() -> None:
    db = _build_session()
    report_id, chunk_ids = _seed_report_with_chunks(db)
    service = RetrievalAuditService(db)

    retrieval_run_id = service.record_retrieval(
        run_id="run-1",
        report_id=report_id,
        query_text="behavior",
        retrieval_mode="hybrid_rrf_stub",
        top_k=2,
        candidates=[
            ScoredChunk(
                chunk_id=chunk_ids[0],
                text="first behavior",
                score_sparse=1.2,
                score_dense=0.4,
                score_fused=0.03,
            ),
            ScoredChunk(
                chunk_id=chunk_ids[1],
                text="second behavior",
                score_sparse=1.0,
                score_dense=0.3,
                score_fused=0.02,
            ),
        ],
    )

    audit_run = db.get(RetrievalAuditRun, retrieval_run_id)
    assert audit_run is not None
    assert audit_run.run_id == "run-1"
    assert audit_run.report_id == report_id
    assert audit_run.query_text == "behavior"
    assert audit_run.query_hash
    assert audit_run.retrieval_mode == "hybrid_rrf_stub"
    assert audit_run.top_k == 2

    candidates = (
        db.execute(
            select(RetrievalCandidate)
            .where(RetrievalCandidate.retrieval_run_id == retrieval_run_id)
            .order_by(RetrievalCandidate.rank)
        )
        .scalars()
        .all()
    )
    assert [candidate.chunk_id for candidate in candidates] == chunk_ids
    assert [candidate.rank for candidate in candidates] == [1, 2]
    assert all(candidate.selected is True for candidate in candidates)


def test_record_retrieval_rejects_unknown_chunk() -> None:
    db = _build_session()
    report_id, _ = _seed_report_with_chunks(db)
    service = RetrievalAuditService(db)

    with pytest.raises(ValueError, match="chunk_id missing-chunk not found"):
        service.record_retrieval(
            run_id="run-unknown",
            report_id=report_id,
            query_text="behavior",
            retrieval_mode="hybrid_rrf_stub",
            top_k=1,
            candidates=[
                ScoredChunk(
                    chunk_id="missing-chunk",
                    text="missing",
                    score_sparse=0.0,
                    score_dense=0.0,
                    score_fused=0.0,
                )
            ],
        )

    assert db.execute(select(RetrievalAuditRun)).scalars().all() == []
    assert db.execute(select(RetrievalCandidate)).scalars().all() == []
```

- [ ] **Step 2: Run failing service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py -q
```

Expected: FAIL because `de_forge.services.retrieval_audit` does not exist.

- [ ] **Step 3: Implement retrieval audit service**

Create `src/de_forge/services/retrieval_audit.py` with:

```python
from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from sqlalchemy.orm import Session

from de_forge.models import Report, ReportChunk, RetrievalAuditRun, RetrievalCandidate
from de_forge.services.retrieval import ScoredChunk


class RetrievalAuditService:
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
    ) -> str:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not query_text:
            raise ValueError("query_text must be non-empty")
        if self.db.get(Report, report_id) is None:
            raise ValueError(f"report_id {report_id} not found")

        candidate_chunk_ids = [candidate.chunk_id for candidate in candidates]
        chunks = {
            chunk.id: chunk
            for chunk in self.db.query(ReportChunk)
            .filter(ReportChunk.id.in_(candidate_chunk_ids))
            .all()
        }
        for chunk_id in candidate_chunk_ids:
            chunk = chunks.get(chunk_id)
            if chunk is None:
                raise ValueError(f"chunk_id {chunk_id} not found")
            if chunk.report_id != report_id:
                raise ValueError(f"chunk_id {chunk_id} does not belong to report_id {report_id}")

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        retrieval_run_id = f"retrieval-{uuid4().hex}"
        audit_run = RetrievalAuditRun(
            id=retrieval_run_id,
            run_id=run_id,
            report_id=report_id,
            query_text=query_text,
            query_hash=sha256(query_text.encode("utf-8")).hexdigest(),
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            created_at=created_at,
        )
        self.db.add(audit_run)
        for rank, candidate in enumerate(candidates, start=1):
            self.db.add(
                RetrievalCandidate(
                    id=f"retrieval-candidate-{uuid4().hex}",
                    retrieval_run_id=retrieval_run_id,
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
        return retrieval_run_id
```

- [ ] **Step 4: Run service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py -q
```

Expected: PASS.

- [ ] **Step 5: Run affected persistence tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/retrieval_audit.py tests/integration/services/test_retrieval_audit.py
git commit -m "feat(retrieval): persist retrieval audit candidates

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Query DB-backed run evidence lineage

**Files:**
- Modify: `src/de_forge/services/retrieval_audit.py`
- Modify: `tests/integration/services/test_retrieval_audit.py`

- [ ] **Step 1: Write failing lineage query test**

Append this test to `tests/integration/services/test_retrieval_audit.py`:

```python
from de_forge.models import EvidenceSpan
from de_forge.services.evidence import EvidenceInput, EvidenceService


def test_get_run_evidence_lineage_returns_db_backed_chunk_and_evidence() -> None:
    db = _build_session()
    report_id, chunk_ids = _seed_report_with_chunks(db)
    audit = RetrievalAuditService(db)
    audit.record_retrieval(
        run_id="run-lineage",
        report_id=report_id,
        query_text="first behavior",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk_ids[0],
                text="first behavior",
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-lineage",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-1",
                chunk_id=chunk_ids[0],
                quote="first behavior",
                char_start=0,
                char_end=14,
                supports_claim="First behavior observed",
                confidence=0.9,
            )
        ],
    )

    lineage = audit.get_run_evidence_lineage("run-lineage")

    assert lineage == {
        "run_id": "run-lineage",
        "items": [
            {
                "evidence_id": "evidence-1",
                "report_id": report_id,
                "chunk_id": chunk_ids[0],
                "quote": "first behavior",
                "char_start": 0,
                "char_end": 14,
                "retrieval_rank": 1,
                "retrieval_score_fused": 0.03,
                "lineage": {
                    "report_id": report_id,
                    "chunk_id": chunk_ids[0],
                    "evidence_id": "evidence-1",
                },
            }
        ],
    }


def test_get_run_evidence_lineage_fails_closed_without_retrieval_audit() -> None:
    db = _build_session()
    report_id, chunk_ids = _seed_report_with_chunks(db)
    EvidenceService(db).persist_evidence(
        report_id=report_id,
        run_id="run-no-audit",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-no-audit",
                chunk_id=chunk_ids[0],
                quote="first behavior",
                char_start=0,
                char_end=14,
                supports_claim="First behavior observed",
                confidence=0.9,
            )
        ],
    )

    with pytest.raises(ValueError, match="retrieval audit lineage missing"):
        RetrievalAuditService(db).get_run_evidence_lineage("run-no-audit")
```

Remove the direct `EvidenceSpan` import if unused after editing.

- [ ] **Step 2: Run failing lineage tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py::test_get_run_evidence_lineage_returns_db_backed_chunk_and_evidence tests/integration/services/test_retrieval_audit.py::test_get_run_evidence_lineage_fails_closed_without_retrieval_audit -q
```

Expected: FAIL because `get_run_evidence_lineage` does not exist.

- [ ] **Step 3: Implement lineage query method**

Add imports to `src/de_forge/services/retrieval_audit.py`:

```python
from sqlalchemy import select

from de_forge.models import EvidenceSpan
```

Add this method to `RetrievalAuditService`:

```python
    def get_run_evidence_lineage(self, run_id: str) -> dict[str, object]:
        evidence_rows = (
            self.db.execute(
                select(EvidenceSpan)
                .where(EvidenceSpan.run_id == run_id)
                .order_by(EvidenceSpan.id)
            )
            .scalars()
            .all()
        )
        if not evidence_rows:
            return {"run_id": run_id, "items": []}

        chunk_ids = [evidence.chunk_id for evidence in evidence_rows]
        candidates = (
            self.db.execute(
                select(RetrievalCandidate)
                .where(RetrievalCandidate.run_id == run_id)
                .where(RetrievalCandidate.chunk_id.in_(chunk_ids))
            )
            .scalars()
            .all()
        )
        candidate_by_chunk = {candidate.chunk_id: candidate for candidate in candidates}
        missing_chunks = [chunk_id for chunk_id in chunk_ids if chunk_id not in candidate_by_chunk]
        if missing_chunks:
            raise ValueError("retrieval audit lineage missing for evidence chunks")

        items = []
        for evidence in evidence_rows:
            candidate = candidate_by_chunk[evidence.chunk_id]
            items.append(
                {
                    "evidence_id": evidence.id,
                    "report_id": evidence.report_id,
                    "chunk_id": evidence.chunk_id,
                    "quote": evidence.quote,
                    "char_start": evidence.char_start,
                    "char_end": evidence.char_end,
                    "retrieval_rank": candidate.rank,
                    "retrieval_score_fused": candidate.score_fused,
                    "lineage": {
                        "report_id": evidence.report_id,
                        "chunk_id": evidence.chunk_id,
                        "evidence_id": evidence.id,
                    },
                }
            )
        return {"run_id": run_id, "items": items}
```

- [ ] **Step 4: Run lineage tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py::test_get_run_evidence_lineage_returns_db_backed_chunk_and_evidence tests/integration/services/test_retrieval_audit.py::test_get_run_evidence_lineage_fails_closed_without_retrieval_audit -q
```

Expected: PASS.

- [ ] **Step 5: Run full retrieval audit service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/retrieval_audit.py tests/integration/services/test_retrieval_audit.py
git commit -m "feat(retrieval): expose evidence lineage from audit records

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Replace placeholder run evidence API with DB-backed lineage

**Files:**
- Modify: `src/de_forge/api/routes/runs.py`
- Create: `tests/integration/api/test_runs_lineage.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/integration/api/test_runs_lineage.py` with:

```python
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from de_forge.api.dependencies import get_db
from de_forge.api.routes.runs import router as runs_router
from de_forge.db.base import Base
from de_forge.models import Report, ReportChunk
from de_forge.services.evidence import EvidenceInput, EvidenceService
from de_forge.services.retrieval import ScoredChunk
from de_forge.services.retrieval_audit import RetrievalAuditService


def _build_client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    db = maker()
    app = FastAPI()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(runs_router)
    return TestClient(app), db


def _seed_lineage(db: Session) -> None:
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    report = Report(
        id="report-api",
        source_type="txt",
        source_uri="report.txt",
        title="report.txt",
        raw_text="api behavior",
        content_hash="hash-api",
        metadata_json="{}",
        status="ingested",
        created_at=created_at,
        updated_at=created_at,
    )
    chunk = ReportChunk(
        id="chunk-api",
        report_id=report.id,
        chunk_index=0,
        section_title=None,
        chunk_text="api behavior",
        char_start=0,
        char_end=12,
        chunk_type="paragraph",
        created_at=created_at,
    )
    db.add(report)
    db.add(chunk)
    db.commit()
    RetrievalAuditService(db).record_retrieval(
        run_id="run-api",
        report_id=report.id,
        query_text="api behavior",
        retrieval_mode="hybrid_rrf_stub",
        top_k=1,
        candidates=[
            ScoredChunk(
                chunk_id=chunk.id,
                text="api behavior",
                score_sparse=1.0,
                score_dense=1.0,
                score_fused=0.03,
            )
        ],
    )
    EvidenceService(db).persist_evidence(
        report_id=report.id,
        run_id="run-api",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-api",
                chunk_id=chunk.id,
                quote="api behavior",
                char_start=0,
                char_end=12,
                supports_claim="API behavior observed",
                confidence=0.9,
            )
        ],
    )


def test_run_evidence_endpoint_returns_persisted_lineage() -> None:
    client, db = _build_client()
    _seed_lineage(db)

    response = client.get("/runs/run-api/evidence")

    assert response.status_code == 200
    assert response.json() == {
        "run_id": "run-api",
        "items": [
            {
                "evidence_id": "evidence-api",
                "report_id": "report-api",
                "chunk_id": "chunk-api",
                "quote": "api behavior",
                "char_start": 0,
                "char_end": 12,
                "retrieval_rank": 1,
                "retrieval_score_fused": 0.03,
                "lineage": {
                    "report_id": "report-api",
                    "chunk_id": "chunk-api",
                    "evidence_id": "evidence-api",
                },
            }
        ],
    }


def test_run_evidence_endpoint_does_not_return_placeholder_for_missing_run() -> None:
    client, _ = _build_client()

    response = client.get("/runs/missing-run/evidence")

    assert response.status_code == 200
    assert response.json() == {"run_id": "missing-run", "items": []}
```

- [ ] **Step 2: Run failing API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_runs_lineage.py -q
```

Expected: FAIL because `/runs/{run_id}/evidence` returns the placeholder `PowerShell -enc AAA` payload and does not accept a DB session.

- [ ] **Step 3: Replace run evidence route implementation**

Update imports in `src/de_forge/api/routes/runs.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from de_forge.api.dependencies import get_db
from de_forge.services.retrieval_audit import RetrievalAuditService
```

Replace `run_evidence` with:

```python
@router.get("/{run_id}/evidence")
def run_evidence(run_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        return RetrievalAuditService(db).get_run_evidence_lineage(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
```

Do not change `start_golden_run`, `run_spec`, `run_portfolio`, or `run_validation` in this task.

- [ ] **Step 4: Run API tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_runs_lineage.py -q
```

Expected: PASS.

- [ ] **Step 5: Run affected API/service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/api/test_runs_lineage.py tests/integration/services/test_retrieval_audit.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/api/routes/runs.py tests/integration/api/test_runs_lineage.py
git commit -m "fix(api): serve run evidence lineage from database

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: Phase verification and audit

**Files:**
- Verify only unless a regression fix is required.

- [ ] **Step 1: Run retrieval lineage tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_retrieval_audit.py tests/integration/api/test_runs_lineage.py -q
```

Expected: PASS.

- [ ] **Step 2: Run evidence citation and review gate regressions**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 3: Run schema/migration regressions**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS.

- [ ] **Step 4: Run broader retrieval/evidence/API selection**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration -q -k "retrieval or evidence or runs"
```

Expected: PASS or only unrelated failures with documented evidence.

- [ ] **Step 5: Run docs preflight**

Run:

```bash
PYTHONPATH="$PWD/src" python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 6: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors in phase files. CRLF warnings for unrelated local Claude settings are not phase failures and must not be staged.

- [ ] **Step 7: Review commit boundary**

Run:

```bash
git status --short
git diff --stat
```

Expected: no uncommitted phase changes. Do not stage or commit `.claude/settings.local.json`, `.claude/worktrees/`, `.claude/scheduled_tasks.lock`, `de_forge.db`, `.env`, cache files, or unrelated docs.

- [ ] **Step 8: Commit only if verification required a tracked fix**

If verification required a fix, commit only related Phase 4 files:

```bash
git add <related phase 4 files>
git commit -m "fix(retrieval): complete audit lineage verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:** Phase 4 design requirements are covered: persisted retrieval runs, persisted candidate chunks, DB-backed run evidence lineage, fail-closed missing audit lineage, migration/schema tests, and phase verification.

**Placeholder scan:** No TODO/TBD/placeholders remain. Every code-changing step includes exact code and commands.

**Type consistency:** `RetrievalAuditService.record_retrieval(...)` accepts `list[ScoredChunk]`; `RetrievalCandidate` score fields match `ScoredChunk`; lineage dictionaries use stable JSON-compatible primitive values.

**Scope control:** This plan does not replace retrieval ranking algorithms, add vector DB dependencies, change citation contracts, or repair later validation/orchestration/API surfaces beyond `/runs/{run_id}/evidence` required for Phase 4 lineage.
