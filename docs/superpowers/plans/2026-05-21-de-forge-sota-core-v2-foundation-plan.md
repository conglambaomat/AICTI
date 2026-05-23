# DE-Forge SOTA Core v2 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic foundation for DE-Forge SOTA Core v2: hashing/idempotency, artifact lineage, database/session foundation, evidence graph primitives, telemetry/ATT&CK detection registries, citation verification, DetectionSpec verification, and proof obligations.

**Architecture:** This plan implements the non-LLM, validator-first core required before any agent or UI work. The output is a tested foundation where artifacts can be persisted with lineage, graph nodes/edges can be queried, citations can be verified exactly, telemetry fields can be validated, DetectionSpecs can be verified, and rule candidates can be blocked unless required proof obligations are proven.

**Tech Stack:** Python 3.11+, FastAPI existing skeleton, Pydantic v2, SQLAlchemy 2.x async-ready models, SQLite local default, pytest, ruff, mypy, uv when available.

> **Commit policy:** Commit steps in this plan are conditional. Execute them only if the user explicitly authorizes commits for the current execution session. Otherwise skip commit commands and report changed files per task.

---

## Scope boundary

The approved spec covers many independent subsystems. This first implementation plan intentionally builds only the deterministic foundation. It does not implement LLM agents, full Sigma compiler, dynamic/adversarial replay, oracle/CTI-REALM adapter, Web UI, or feedback regression execution. Those must be separate plans after this foundation passes.

This plan builds working, testable software on its own:

1. Stable hashing and idempotency primitives.
2. SQLAlchemy base/session and artifact lineage models.
3. Evidence graph models and query service.
4. Deterministic TXT ingestion/chunking and citation verification.
5. ATT&CK Detection Strategy / Analytic / Data Component registry.
6. Multi-platform telemetry registry.
7. Formal DetectionSpec schema and verifier.
8. Proof obligation schema/service/verifier.

## File structure map

Create or modify these files:

- `src/de_forge/core/hashing.py` — canonical JSON serialization and stable snapshot hashes.
- `src/de_forge/core/idempotency.py` — deterministic idempotency keys.
- `src/de_forge/core/errors.py` — domain exceptions for validation failures.
- `src/de_forge/db/base.py` — SQLAlchemy declarative base.
- `src/de_forge/db/session.py` — engine/session factory helpers.
- `src/de_forge/models/artifact.py` — persisted artifact lineage model.
- `src/de_forge/models/report.py` — report and chunk persistence models.
- `src/de_forge/models/evidence_graph.py` — graph node/edge persistence models.
- `src/de_forge/schemas/artifact.py` — artifact schema/enums.
- `src/de_forge/schemas/evidence_graph.py` — graph node/edge schema/enums.
- `src/de_forge/schemas/attack_detection.py` — technique/strategy/analytic/data component schemas.
- `src/de_forge/schemas/telemetry.py` — telemetry source/field schemas.
- `src/de_forge/schemas/detection_spec.py` — DetectionSpec contract.
- `src/de_forge/schemas/proof_obligation.py` — proof obligation contract.
- `src/de_forge/services/artifact_store.py` — artifact lineage persistence service.
- `src/de_forge/services/evidence_graph.py` — graph persistence/query service.
- `src/de_forge/services/chunking.py` — deterministic text chunking.
- `src/de_forge/services/citation_verifier.py` — exact quote/offset verification.
- `src/de_forge/services/attack_detection_registry.py` — curated initial ATT&CK detection registry.
- `src/de_forge/services/telemetry_registry.py` — curated initial telemetry registry.
- `src/de_forge/services/detection_spec_verifier.py` — formal DetectionSpec verification.
- `src/de_forge/services/proof_obligation_service.py` — proof generation and verification.
- `tests/unit/core/test_hashing_idempotency.py`.
- `tests/unit/services/test_chunking_citation.py`.
- `tests/unit/services/test_attack_telemetry_registry.py`.
- `tests/unit/services/test_detection_spec_verifier.py`.
- `tests/unit/services/test_proof_obligations.py`.
- `tests/integration/db/test_artifact_graph_persistence.py`.

---

### Task 1: Stable hashing and idempotency primitives

**Files:**
- Create: `src/de_forge/core/hashing.py`
- Create: `src/de_forge/core/idempotency.py`
- Test: `tests/unit/core/test_hashing_idempotency.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/core/test_hashing_idempotency.py`:

```python
from de_forge.core.hashing import canonical_json, snapshot_hash, verify_snapshot_hash
from de_forge.core.idempotency import make_idempotency_key


def test_canonical_json_sorts_keys_and_removes_whitespace() -> None:
    payload = {"b": 2, "a": {"d": 4, "c": 3}}

    assert canonical_json(payload) == '{"a":{"c":3,"d":4},"b":2}'


def test_snapshot_hash_is_stable_for_equivalent_payloads() -> None:
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}

    assert snapshot_hash(left) == snapshot_hash(right)


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload = {"claim": "safe"}
    digest = snapshot_hash(payload)

    assert verify_snapshot_hash(payload, digest) is True
    assert verify_snapshot_hash({"claim": "changed"}, digest) is False


def test_idempotency_key_includes_stage_identifier() -> None:
    payload = {"report_id": "r1", "stage": "ingest"}

    ingest_key = make_idempotency_key("ingestion.chunk", payload)
    evidence_key = make_idempotency_key("evidence.extract", payload)

    assert ingest_key.startswith("idem_")
    assert evidence_key.startswith("idem_")
    assert ingest_key != evidence_key


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    first = make_idempotency_key("stage", {"b": 2, "a": 1})
    second = make_idempotency_key("stage", {"a": 1, "b": 2})

    assert first == second
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/core/test_hashing_idempotency.py -v
```

Expected: FAIL with import errors for `de_forge.core.hashing` and `de_forge.core.idempotency`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/core/hashing.py`:

```python
"""Stable hashing helpers for persisted artifact snapshots."""

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    """Return a deterministic JSON representation of a payload."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def snapshot_hash(payload: Any) -> str:
    """Return a SHA-256 hash for a canonicalized payload."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def verify_snapshot_hash(payload: Any, expected_hash: str) -> bool:
    """Return whether a payload matches a previously stored snapshot hash."""
    return snapshot_hash(payload) == expected_hash
```

Create `src/de_forge/core/idempotency.py`:

```python
"""Deterministic idempotency key helpers."""

import hashlib
from typing import Any

from de_forge.core.hashing import canonical_json


def make_idempotency_key(stage_identifier: str, payload: Any) -> str:
    """Return a deterministic idempotency key scoped to a pipeline stage."""
    canonical = canonical_json(payload)
    digest = hashlib.sha256(f"{stage_identifier}|{canonical}".encode("utf-8")).hexdigest()
    return f"idem_{digest}"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/core/test_hashing_idempotency.py -v
```

Expected: PASS, 5 tests passed.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/core/test_hashing_idempotency.py src/de_forge/core/hashing.py src/de_forge/core/idempotency.py
git commit -m "feat(core): add stable hashing and idempotency primitives"
```

---

### Task 2: Domain errors and artifact lineage schemas

**Files:**
- Create: `src/de_forge/core/errors.py`
- Create: `src/de_forge/schemas/artifact.py`
- Test: `tests/unit/core/test_artifact_schema.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/core/test_artifact_schema.py`:

```python
import pytest
from pydantic import ValidationError

from de_forge.schemas.artifact import ArtifactCreate, ArtifactKind


def test_artifact_create_requires_lineage_hashes() -> None:
    artifact = ArtifactCreate(
        run_id="run_1",
        kind=ArtifactKind.REPORT,
        stage="ingestion",
        payload={"name": "report.txt"},
        input_hash="in_hash",
        output_hash="out_hash",
        parent_artifact_ids=[],
        created_by="system",
    )

    assert artifact.kind == ArtifactKind.REPORT
    assert artifact.parent_artifact_ids == []


def test_artifact_create_rejects_empty_stage() -> None:
    with pytest.raises(ValidationError):
        ArtifactCreate(
            run_id="run_1",
            kind=ArtifactKind.REPORT,
            stage="",
            payload={},
            input_hash="in_hash",
            output_hash="out_hash",
            parent_artifact_ids=[],
            created_by="system",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/core/test_artifact_schema.py -v
```

Expected: FAIL with import error for `de_forge.schemas.artifact`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/core/errors.py`:

```python
"""Domain exceptions for DE-Forge validation and orchestration."""


class DeForgeError(Exception):
    """Base exception for DE-Forge domain errors."""


class ValidationGateError(DeForgeError):
    """Raised when a deterministic validation gate fails."""


class CitationVerificationError(ValidationGateError):
    """Raised when a citation quote or offset cannot be verified."""


class ProofObligationError(ValidationGateError):
    """Raised when required proof obligations are not proven."""
```

Create `src/de_forge/schemas/artifact.py`:

```python
"""Schemas for persisted pipeline artifacts and lineage."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ArtifactKind(StrEnum):
    REPORT = "report"
    CHUNK = "chunk"
    EVIDENCE_GRAPH = "evidence_graph"
    DETECTION_SPEC = "detection_spec"
    PROOF_OBLIGATION = "proof_obligation"
    RULE_CANDIDATE = "rule_candidate"
    VALIDATION_RESULT = "validation_result"


class ArtifactCreate(BaseModel):
    run_id: str
    kind: ArtifactKind
    stage: str
    payload: dict[str, Any]
    input_hash: str
    output_hash: str
    parent_artifact_ids: list[str] = Field(default_factory=list)
    created_by: str

    @field_validator("run_id", "stage", "input_hash", "output_hash", "created_by")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/core/test_artifact_schema.py -v
```

Expected: PASS, 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/core/test_artifact_schema.py src/de_forge/core/errors.py src/de_forge/schemas/artifact.py
git commit -m "feat(core): add artifact lineage schemas and domain errors"
```

---

### Task 3: SQLAlchemy base, session, and artifact persistence

**Files:**
- Create: `src/de_forge/db/base.py`
- Create: `src/de_forge/db/session.py`
- Create: `src/de_forge/models/artifact.py`
- Create: `src/de_forge/services/artifact_store.py`
- Test: `tests/integration/db/test_artifact_graph_persistence.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/db/test_artifact_graph_persistence.py`:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.models.artifact import Artifact
from de_forge.schemas.artifact import ArtifactCreate, ArtifactKind
from de_forge.services.artifact_store import ArtifactStore


def test_artifact_store_persists_lineage() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        store = ArtifactStore(session)
        artifact = store.create(
            ArtifactCreate(
                run_id="run_1",
                kind=ArtifactKind.REPORT,
                stage="ingestion",
                payload={"filename": "report.txt"},
                input_hash="input_hash",
                output_hash="output_hash",
                parent_artifact_ids=[],
                created_by="system",
            )
        )
        session.commit()

        loaded = session.scalar(select(Artifact).where(Artifact.id == artifact.id))

    assert loaded is not None
    assert loaded.run_id == "run_1"
    assert loaded.kind == "report"
    assert loaded.payload["filename"] == "report.txt"
    assert loaded.parent_artifact_ids == []
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/db/test_artifact_graph_persistence.py::test_artifact_store_persists_lineage -v
```

Expected: FAIL with import error for `de_forge.db.base` or `de_forge.models.artifact`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/db/base.py`:

```python
"""SQLAlchemy declarative base."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
```

Create `src/de_forge/db/session.py`:

```python
"""Database engine and session helpers."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from de_forge.core.config import settings

engine = create_engine(settings.database_url.replace("sqlite:///", "sqlite+pysqlite:///"))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Iterator[Session]:
    """Yield a database session for FastAPI dependencies."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

Create `src/de_forge/models/artifact.py`:

```python
"""Artifact lineage persistence models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class Artifact(Base):
    """Persisted pipeline artifact with lineage and snapshot hashes."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"artifact_{uuid.uuid4().hex}")
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String, nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_hash: Mapped[str] = mapped_column(String, nullable=False)
    output_hash: Mapped[str] = mapped_column(String, nullable=False)
    parent_artifact_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

Create `src/de_forge/services/artifact_store.py`:

```python
"""Persistence service for pipeline artifacts."""

from sqlalchemy.orm import Session

from de_forge.models.artifact import Artifact
from de_forge.schemas.artifact import ArtifactCreate


class ArtifactStore:
    """Create and query pipeline artifacts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, artifact: ArtifactCreate) -> Artifact:
        record = Artifact(
            run_id=artifact.run_id,
            kind=artifact.kind.value,
            stage=artifact.stage,
            payload=artifact.payload,
            input_hash=artifact.input_hash,
            output_hash=artifact.output_hash,
            parent_artifact_ids=artifact.parent_artifact_ids,
            created_by=artifact.created_by,
        )
        self.session.add(record)
        self.session.flush()
        return record
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/db/test_artifact_graph_persistence.py::test_artifact_store_persists_lineage -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/db src/de_forge/models/artifact.py src/de_forge/services/artifact_store.py tests/integration/db/test_artifact_graph_persistence.py
git commit -m "feat(db): add artifact lineage persistence"
```

---

### Task 4: Evidence graph schemas, models, and query service

**Files:**
- Create: `src/de_forge/models/evidence_graph.py`
- Create: `src/de_forge/schemas/evidence_graph.py`
- Create: `src/de_forge/services/evidence_graph.py`
- Modify: `tests/integration/db/test_artifact_graph_persistence.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/db/test_artifact_graph_persistence.py`:

```python
from de_forge.models.evidence_graph import GraphEdge, GraphNode
from de_forge.schemas.evidence_graph import EdgeType, GraphNodeCreate, NodeType
from de_forge.services.evidence_graph import EvidenceGraphService


def test_evidence_graph_persists_support_path() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        graph = EvidenceGraphService(session)
        quote = graph.create_node(
            GraphNodeCreate(
                run_id="run_1",
                node_type=NodeType.EVIDENCE_QUOTE,
                payload={"quote": "PowerShell executed an encoded command"},
                source="report",
                confidence=1.0,
                created_by="test",
            )
        )
        behavior = graph.create_node(
            GraphNodeCreate(
                run_id="run_1",
                node_type=NodeType.BEHAVIOR,
                payload={"label": "encoded PowerShell execution"},
                source="evidence_agent",
                confidence=0.95,
                created_by="test",
            )
        )
        edge = graph.create_edge(
            run_id="run_1",
            source_node_id=quote.id,
            target_node_id=behavior.id,
            edge_type=EdgeType.SUPPORTS,
            supporting_evidence_ids=[quote.id],
            confidence=0.95,
            created_by="test",
        )
        session.commit()

        support_edges = graph.outgoing_edges(quote.id, EdgeType.SUPPORTS)

    assert edge.id is not None
    assert len(support_edges) == 1
    assert support_edges[0].target_node_id == behavior.id
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/db/test_artifact_graph_persistence.py::test_evidence_graph_persists_support_path -v
```

Expected: FAIL with import error for `de_forge.models.evidence_graph`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/evidence_graph.py`:

```python
"""Schemas for evidence graph nodes and edges."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class NodeType(StrEnum):
    REPORT = "report"
    CHUNK = "chunk"
    EVIDENCE_QUOTE = "evidence_quote"
    BEHAVIOR = "behavior"
    ENTITY = "entity"
    IOC = "ioc"
    ATTACK_TECHNIQUE = "attack_technique"
    DETECTION_STRATEGY = "detection_strategy"
    ANALYTIC = "analytic"
    DATA_COMPONENT = "data_component"
    TELEMETRY_SOURCE = "telemetry_source"
    TELEMETRY_FIELD = "telemetry_field"
    DETECTION_SPEC = "detection_spec"
    RULE_CANDIDATE = "rule_candidate"
    PROOF_OBLIGATION = "proof_obligation"


class EdgeType(StrEnum):
    SUPPORTS = "supports"
    MENTIONS = "mentions"
    MAPS_TO = "maps_to"
    REQUIRES = "requires"
    IMPLEMENTS = "implements"
    VALIDATED_BY = "validated_by"
    DERIVED_FROM = "derived_from"
    CONTRADICTS = "contradicts"
    SATISFIES = "satisfies"
    FAILED_BY = "failed_by"


class GraphNodeCreate(BaseModel):
    run_id: str
    node_type: NodeType
    payload: dict[str, Any]
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_by: str

    @field_validator("run_id", "source", "created_by")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value
```

Create `src/de_forge/models/evidence_graph.py`:

```python
"""Evidence graph persistence models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class GraphNode(Base):
    """A typed node in the evidence graph."""

    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"node_{uuid.uuid4().hex}")
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class GraphEdge(Base):
    """A typed relationship between two graph nodes."""

    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"edge_{uuid.uuid4().hex}")
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    target_node_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    supporting_evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

Create `src/de_forge/services/evidence_graph.py`:

```python
"""Persistence and query service for the evidence graph."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models.evidence_graph import GraphEdge, GraphNode
from de_forge.schemas.evidence_graph import EdgeType, GraphNodeCreate


class EvidenceGraphService:
    """Create graph nodes and edges and query support relationships."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_node(self, node: GraphNodeCreate) -> GraphNode:
        record = GraphNode(
            run_id=node.run_id,
            node_type=node.node_type.value,
            payload=node.payload,
            source=node.source,
            confidence=node.confidence,
            created_by=node.created_by,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def create_edge(
        self,
        run_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: EdgeType,
        supporting_evidence_ids: list[str],
        confidence: float,
        created_by: str,
    ) -> GraphEdge:
        record = GraphEdge(
            run_id=run_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type.value,
            supporting_evidence_ids=supporting_evidence_ids,
            confidence=confidence,
            created_by=created_by,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def outgoing_edges(self, node_id: str, edge_type: EdgeType) -> list[GraphEdge]:
        statement = select(GraphEdge).where(
            GraphEdge.source_node_id == node_id,
            GraphEdge.edge_type == edge_type.value,
        )
        return list(self.session.scalars(statement).all())
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/db/test_artifact_graph_persistence.py -v
```

Expected: PASS for artifact and evidence graph tests.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/models/evidence_graph.py src/de_forge/schemas/evidence_graph.py src/de_forge/services/evidence_graph.py tests/integration/db/test_artifact_graph_persistence.py
git commit -m "feat(graph): add evidence graph persistence and support queries"
```

---

### Task 5: Deterministic chunking and citation verification

**Files:**
- Create: `src/de_forge/services/chunking.py`
- Create: `src/de_forge/services/citation_verifier.py`
- Test: `tests/unit/services/test_chunking_citation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_chunking_citation.py`:

```python
import pytest

from de_forge.core.errors import CitationVerificationError
from de_forge.services.chunking import chunk_text
from de_forge.services.citation_verifier import verify_quote_span


def test_chunk_text_is_deterministic_with_offsets() -> None:
    text = "alpha beta gamma delta epsilon"

    first = chunk_text(report_id="report_1", text=text, max_chars=12, overlap_chars=3)
    second = chunk_text(report_id="report_1", text=text, max_chars=12, overlap_chars=3)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert first[0].start_offset == 0
    assert text[first[0].start_offset:first[0].end_offset] == first[0].text


def test_verify_quote_span_accepts_exact_offsets() -> None:
    chunk_text_value = "PowerShell executed an encoded command"
    quote = "encoded command"
    start = chunk_text_value.index(quote)
    end = start + len(quote)

    result = verify_quote_span(
        chunk_text=chunk_text_value,
        quote=quote,
        start_offset=start,
        end_offset=end,
    )

    assert result is True


def test_verify_quote_span_rejects_wrong_offsets() -> None:
    with pytest.raises(CitationVerificationError):
        verify_quote_span(
            chunk_text="PowerShell executed an encoded command",
            quote="encoded command",
            start_offset=0,
            end_offset=15,
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_chunking_citation.py -v
```

Expected: FAIL with import error for `de_forge.services.chunking`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/chunking.py`:

```python
"""Deterministic text chunking for report ingestion."""

from dataclasses import dataclass

from de_forge.core.hashing import snapshot_hash


@dataclass(frozen=True)
class TextChunk:
    id: str
    report_id: str
    text: str
    start_offset: int
    end_offset: int
    index: int


def chunk_text(report_id: str, text: str, max_chars: int = 2000, overlap_chars: int = 200) -> list[TextChunk]:
    """Split text into deterministic overlapping chunks with character offsets."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than max_chars")

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_body = text[start:end]
        chunk_hash = snapshot_hash({"report_id": report_id, "start": start, "end": end, "text": chunk_body})[:16]
        chunks.append(
            TextChunk(
                id=f"chunk_{chunk_hash}",
                report_id=report_id,
                text=chunk_body,
                start_offset=start,
                end_offset=end,
                index=index,
            )
        )
        if end == len(text):
            break
        start = end - overlap_chars
        index += 1
    return chunks
```

Create `src/de_forge/services/citation_verifier.py`:

```python
"""Exact citation verification for evidence quotes."""

from de_forge.core.errors import CitationVerificationError


def verify_quote_span(chunk_text: str, quote: str, start_offset: int, end_offset: int) -> bool:
    """Verify that quote exactly matches chunk text at the supplied offsets."""
    if start_offset < 0 or end_offset > len(chunk_text) or start_offset >= end_offset:
        raise CitationVerificationError("citation offsets are outside chunk bounds")
    observed = chunk_text[start_offset:end_offset]
    if observed != quote:
        raise CitationVerificationError("citation quote does not match chunk text at offsets")
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_chunking_citation.py -v
```

Expected: PASS, 3 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/chunking.py src/de_forge/services/citation_verifier.py tests/unit/services/test_chunking_citation.py
git commit -m "feat(ingestion): add deterministic chunking and citation verification"
```

---

### Task 6: ATT&CK detection and telemetry registry schemas/services

**Files:**
- Create: `src/de_forge/schemas/attack_detection.py`
- Create: `src/de_forge/schemas/telemetry.py`
- Create: `src/de_forge/services/attack_detection_registry.py`
- Create: `src/de_forge/services/telemetry_registry.py`
- Test: `tests/unit/services/test_attack_telemetry_registry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_attack_telemetry_registry.py`:

```python
import pytest

from de_forge.services.attack_detection_registry import AttackDetectionRegistry
from de_forge.services.telemetry_registry import TelemetryRegistry


def test_attack_registry_maps_technique_to_detection_strategy_analytic_and_data_component() -> None:
    registry = AttackDetectionRegistry.default()

    links = registry.links_for_technique("T1059.001")

    assert links[0].technique_id == "T1059.001"
    assert links[0].detection_strategy_id == "ds_command_line_behavior"
    assert links[0].analytic_id == "analytic_encoded_powershell"
    assert links[0].data_component_id == "process_creation"


def test_telemetry_registry_accepts_known_process_creation_fields() -> None:
    registry = TelemetryRegistry.default()

    assert registry.field_exists("sysmon_eid_1", "CommandLine") is True
    assert registry.field_exists("windows_security_4688", "NewProcessName") is True


def test_telemetry_registry_rejects_unknown_field() -> None:
    registry = TelemetryRegistry.default()

    assert registry.field_exists("sysmon_eid_1", "DefinitelyNotAField") is False


def test_telemetry_registry_requires_known_source() -> None:
    registry = TelemetryRegistry.default()

    with pytest.raises(KeyError):
        registry.fields_for_source("unknown_source")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_attack_telemetry_registry.py -v
```

Expected: FAIL with import errors for registry services.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/attack_detection.py`:

```python
"""Schemas for ATT&CK detection strategy modeling."""

from pydantic import BaseModel


class TechniqueDetectionLink(BaseModel):
    technique_id: str
    detection_strategy_id: str
    analytic_id: str
    data_component_id: str
```

Create `src/de_forge/schemas/telemetry.py`:

```python
"""Schemas for telemetry sources and fields."""

from pydantic import BaseModel


class TelemetryField(BaseModel):
    source_id: str
    field_name: str
    field_type: str
    required: bool = False


class TelemetrySource(BaseModel):
    source_id: str
    display_name: str
    platform: str
    fields: list[TelemetryField]
```

Create `src/de_forge/services/attack_detection_registry.py`:

```python
"""Curated ATT&CK detection strategy registry."""

from de_forge.schemas.attack_detection import TechniqueDetectionLink


class AttackDetectionRegistry:
    """Map ATT&CK techniques to detection strategies, analytics, and data components."""

    def __init__(self, links: list[TechniqueDetectionLink]) -> None:
        self.links = links

    @classmethod
    def default(cls) -> "AttackDetectionRegistry":
        return cls(
            links=[
                TechniqueDetectionLink(
                    technique_id="T1059.001",
                    detection_strategy_id="ds_command_line_behavior",
                    analytic_id="analytic_encoded_powershell",
                    data_component_id="process_creation",
                ),
                TechniqueDetectionLink(
                    technique_id="T1059.003",
                    detection_strategy_id="ds_command_line_behavior",
                    analytic_id="analytic_suspicious_cmd_shell",
                    data_component_id="process_creation",
                ),
                TechniqueDetectionLink(
                    technique_id="T1105",
                    detection_strategy_id="ds_network_transfer_behavior",
                    analytic_id="analytic_suspicious_external_download",
                    data_component_id="network_connection",
                ),
            ]
        )

    def links_for_technique(self, technique_id: str) -> list[TechniqueDetectionLink]:
        return [link for link in self.links if link.technique_id == technique_id]
```

Create `src/de_forge/services/telemetry_registry.py`:

```python
"""Curated multi-platform telemetry registry."""

from de_forge.schemas.telemetry import TelemetryField, TelemetrySource


class TelemetryRegistry:
    """Validate telemetry sources and fields."""

    def __init__(self, sources: list[TelemetrySource]) -> None:
        self.sources = {source.source_id: source for source in sources}

    @classmethod
    def default(cls) -> "TelemetryRegistry":
        return cls(
            sources=[
                TelemetrySource(
                    source_id="sysmon_eid_1",
                    display_name="Sysmon Event ID 1 Process Creation",
                    platform="windows",
                    fields=[
                        TelemetryField(source_id="sysmon_eid_1", field_name="Image", field_type="string", required=True),
                        TelemetryField(source_id="sysmon_eid_1", field_name="CommandLine", field_type="string", required=True),
                        TelemetryField(source_id="sysmon_eid_1", field_name="ParentImage", field_type="string"),
                        TelemetryField(source_id="sysmon_eid_1", field_name="OriginalFileName", field_type="string"),
                    ],
                ),
                TelemetrySource(
                    source_id="windows_security_4688",
                    display_name="Windows Security 4688 Process Creation",
                    platform="windows",
                    fields=[
                        TelemetryField(source_id="windows_security_4688", field_name="NewProcessName", field_type="string", required=True),
                        TelemetryField(source_id="windows_security_4688", field_name="CommandLine", field_type="string"),
                        TelemetryField(source_id="windows_security_4688", field_name="ParentProcessName", field_type="string"),
                    ],
                ),
                TelemetrySource(
                    source_id="linux_auditd_execve",
                    display_name="Linux auditd execve",
                    platform="linux",
                    fields=[
                        TelemetryField(source_id="linux_auditd_execve", field_name="exe", field_type="string", required=True),
                        TelemetryField(source_id="linux_auditd_execve", field_name="argc", field_type="integer"),
                        TelemetryField(source_id="linux_auditd_execve", field_name="a0", field_type="string"),
                    ],
                ),
                TelemetrySource(
                    source_id="zeek_conn",
                    display_name="Zeek conn.log",
                    platform="network",
                    fields=[
                        TelemetryField(source_id="zeek_conn", field_name="id.orig_h", field_type="string", required=True),
                        TelemetryField(source_id="zeek_conn", field_name="id.resp_h", field_type="string", required=True),
                        TelemetryField(source_id="zeek_conn", field_name="id.resp_p", field_type="integer"),
                    ],
                ),
            ]
        )

    def fields_for_source(self, source_id: str) -> list[TelemetryField]:
        if source_id not in self.sources:
            raise KeyError(source_id)
        return self.sources[source_id].fields

    def field_exists(self, source_id: str, field_name: str) -> bool:
        fields = self.fields_for_source(source_id)
        return any(field.field_name == field_name for field in fields)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_attack_telemetry_registry.py -v
```

Expected: PASS, 4 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/attack_detection.py src/de_forge/schemas/telemetry.py src/de_forge/services/attack_detection_registry.py src/de_forge/services/telemetry_registry.py tests/unit/services/test_attack_telemetry_registry.py
git commit -m "feat(registry): add attack detection and telemetry registries"
```

---

### Task 7: Formal DetectionSpec schema and verifier

**Files:**
- Create: `src/de_forge/schemas/detection_spec.py`
- Create: `src/de_forge/services/detection_spec_verifier.py`
- Test: `tests/unit/services/test_detection_spec_verifier.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_detection_spec_verifier.py`:

```python
import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.detection_spec import DetectionCondition, DetectionSpec, TelemetryRequirement
from de_forge.services.detection_spec_verifier import DetectionSpecVerifier
from de_forge.services.telemetry_registry import TelemetryRegistry


def valid_spec() -> DetectionSpec:
    return DetectionSpec(
        id="spec_1",
        evidence_ids=["evidence_1"],
        behavior_ids=["behavior_1"],
        attack_techniques=["T1059.001"],
        detection_strategies=["ds_command_line_behavior"],
        analytics=["analytic_encoded_powershell"],
        data_components=["process_creation"],
        telemetry_requirements=[
            TelemetryRequirement(source_id="sysmon_eid_1", required_fields=["Image", "CommandLine"])
        ],
        allowed_fields=["Image", "CommandLine", "ParentImage"],
        logic_requirements=[
            DetectionCondition(field="CommandLine", operator="contains_any", values=["-enc", "-EncodedCommand"], evidence_ids=["evidence_1"])
        ],
        false_positive_hypotheses=["administrative encoded PowerShell usage"],
        test_plan=["positive event with encoded command", "benign PowerShell without encoded command"],
        abstain_reason=None,
        verified=False,
    )


def test_detection_spec_verifier_marks_valid_spec_verified() -> None:
    verifier = DetectionSpecVerifier(TelemetryRegistry.default())
    spec = valid_spec()

    verified = verifier.verify(spec)

    assert verified.verified is True


def test_detection_spec_rejects_unknown_telemetry_field() -> None:
    verifier = DetectionSpecVerifier(TelemetryRegistry.default())
    spec = valid_spec().model_copy(update={"allowed_fields": ["DefinitelyNotAField"]})

    with pytest.raises(ValidationGateError):
        verifier.verify(spec)


def test_detection_spec_rejects_logic_without_evidence() -> None:
    verifier = DetectionSpecVerifier(TelemetryRegistry.default())
    spec = valid_spec().model_copy(
        update={
            "logic_requirements": [
                DetectionCondition(field="CommandLine", operator="contains", values=["powershell"], evidence_ids=[])
            ]
        }
    )

    with pytest.raises(ValidationGateError):
        verifier.verify(spec)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_detection_spec_verifier.py -v
```

Expected: FAIL with import error for DetectionSpec schema/service.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/detection_spec.py`:

```python
"""Formal DetectionSpec contract."""

from pydantic import BaseModel, Field


class TelemetryRequirement(BaseModel):
    source_id: str
    required_fields: list[str] = Field(min_length=1)


class DetectionCondition(BaseModel):
    field: str
    operator: str
    values: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class DetectionSpec(BaseModel):
    id: str
    evidence_ids: list[str]
    behavior_ids: list[str]
    attack_techniques: list[str]
    detection_strategies: list[str]
    analytics: list[str]
    data_components: list[str]
    telemetry_requirements: list[TelemetryRequirement]
    allowed_fields: list[str]
    logic_requirements: list[DetectionCondition]
    false_positive_hypotheses: list[str]
    test_plan: list[str]
    abstain_reason: str | None = None
    verified: bool = False
```

Create `src/de_forge/services/detection_spec_verifier.py`:

```python
"""Formal DetectionSpec verification gates."""

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.detection_spec import DetectionSpec
from de_forge.services.telemetry_registry import TelemetryRegistry


class DetectionSpecVerifier:
    """Verify DetectionSpec evidence, telemetry, and logic constraints."""

    def __init__(self, telemetry_registry: TelemetryRegistry) -> None:
        self.telemetry_registry = telemetry_registry

    def verify(self, spec: DetectionSpec) -> DetectionSpec:
        if not spec.evidence_ids:
            raise ValidationGateError("DetectionSpec requires evidence")
        if not spec.behavior_ids:
            raise ValidationGateError("DetectionSpec requires behavior ids")
        if not spec.attack_techniques:
            raise ValidationGateError("DetectionSpec requires ATT&CK techniques")
        if not spec.telemetry_requirements:
            raise ValidationGateError("DetectionSpec requires telemetry requirements")

        available_fields: set[str] = set()
        for requirement in spec.telemetry_requirements:
            source_fields = self.telemetry_registry.fields_for_source(requirement.source_id)
            source_field_names = {field.field_name for field in source_fields}
            for required_field in requirement.required_fields:
                if required_field not in source_field_names:
                    raise ValidationGateError(f"required field {required_field} missing from {requirement.source_id}")
            available_fields.update(source_field_names)

        for field in spec.allowed_fields:
            if field not in available_fields:
                raise ValidationGateError(f"allowed field {field} is not available in selected telemetry")

        evidence_ids = set(spec.evidence_ids)
        for condition in spec.logic_requirements:
            if condition.field not in spec.allowed_fields:
                raise ValidationGateError(f"logic field {condition.field} is not allowed")
            if not set(condition.evidence_ids).issubset(evidence_ids):
                raise ValidationGateError("logic condition references evidence outside DetectionSpec")

        return spec.model_copy(update={"verified": True})
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_detection_spec_verifier.py -v
```

Expected: PASS, 3 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/detection_spec.py src/de_forge/services/detection_spec_verifier.py tests/unit/services/test_detection_spec_verifier.py
git commit -m "feat(spec): add formal DetectionSpec verifier"
```

---

### Task 8: Proof obligation schema, generation, and verification

**Files:**
- Create: `src/de_forge/schemas/proof_obligation.py`
- Create: `src/de_forge/services/proof_obligation_service.py`
- Test: `tests/unit/services/test_proof_obligations.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_proof_obligations.py`:

```python
import pytest

from de_forge.core.errors import ProofObligationError
from de_forge.schemas.proof_obligation import ProofObligationStatus, ProofObligationType
from de_forge.services.proof_obligation_service import ProofObligationService


def test_required_proof_obligations_are_generated_for_rule_candidate() -> None:
    service = ProofObligationService()

    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")

    obligation_types = {obligation.claim_type for obligation in obligations}
    assert ProofObligationType.DETECTS_REPORT_BEHAVIOR in obligation_types
    assert ProofObligationType.NOT_OVERBROAD in obligation_types
    assert ProofObligationType.TELEMETRY_FIELDS_EXIST in obligation_types
    assert ProofObligationType.CITATION_FAITHFUL in obligation_types


def test_candidate_cannot_be_selected_with_unknown_required_obligation() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")

    with pytest.raises(ProofObligationError):
        service.verify_selectable(obligations)


def test_candidate_selectable_when_all_required_obligations_are_proven() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    proven = [obligation.model_copy(update={"status": ProofObligationStatus.PROVEN}) for obligation in obligations]

    assert service.verify_selectable(proven) is True


def test_not_applicable_requires_justification() -> None:
    service = ProofObligationService()
    obligations = service.generate_required(rule_candidate_id="candidate_1", run_id="run_1")
    invalid = [
        obligations[0].model_copy(update={"status": ProofObligationStatus.NOT_APPLICABLE, "justification": None})
    ]

    with pytest.raises(ProofObligationError):
        service.verify_selectable(invalid)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_proof_obligations.py -v
```

Expected: FAIL with import error for proof obligation schema/service.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/proof_obligation.py`:

```python
"""Proof obligation contracts for selectable rule candidates."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ProofObligationType(StrEnum):
    DETECTS_REPORT_BEHAVIOR = "detects_report_behavior"
    NOT_OVERBROAD = "not_overbroad"
    TELEMETRY_FIELDS_EXIST = "telemetry_fields_exist"
    POSITIVE_TESTS_PASS = "positive_tests_pass"
    BENIGN_BASELINE_NOT_MATCHED = "benign_baseline_not_matched"
    CITATION_FAITHFUL = "citation_faithful"
    ORACLE_EXPECTATIONS_SATISFIED = "oracle_expectations_satisfied"
    REGRESSION_SAFE = "regression_safe"


class ProofObligationStatus(StrEnum):
    PROVEN = "proven"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ProofObligation(BaseModel):
    run_id: str
    rule_candidate_id: str
    claim_type: ProofObligationType
    claim_text: str
    required_artifact_types: list[str] = Field(min_length=1)
    status: ProofObligationStatus = ProofObligationStatus.UNKNOWN
    justification: str | None = None
```

Create `src/de_forge/services/proof_obligation_service.py`:

```python
"""Generate and verify proof obligations for rule candidates."""

from de_forge.core.errors import ProofObligationError
from de_forge.schemas.proof_obligation import ProofObligation, ProofObligationStatus, ProofObligationType


class ProofObligationService:
    """Manage required proof obligations for final candidate selection."""

    def generate_required(self, rule_candidate_id: str, run_id: str) -> list[ProofObligation]:
        return [
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.DETECTS_REPORT_BEHAVIOR,
                claim_text="Rule detects the behavior described in report evidence.",
                required_artifact_types=["evidence_quote", "detection_logic", "positive_test"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.NOT_OVERBROAD,
                claim_text="Rule is not overbroad for normal benign behavior.",
                required_artifact_types=["benign_baseline", "false_positive_analysis"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.TELEMETRY_FIELDS_EXIST,
                claim_text="All rule fields exist in selected telemetry.",
                required_artifact_types=["telemetry_registry_check"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.POSITIVE_TESTS_PASS,
                claim_text="Rule passes expected positive test cases.",
                required_artifact_types=["dynamic_test_run"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.BENIGN_BASELINE_NOT_MATCHED,
                claim_text="Rule does not match benign baseline beyond threshold.",
                required_artifact_types=["benign_replay_run"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.CITATION_FAITHFUL,
                claim_text="Evidence citations are exact and claim-supporting.",
                required_artifact_types=["citation_verification"],
            ),
            ProofObligation(
                run_id=run_id,
                rule_candidate_id=rule_candidate_id,
                claim_type=ProofObligationType.REGRESSION_SAFE,
                claim_text="Candidate does not violate previous regression gates.",
                required_artifact_types=["regression_run"],
            ),
        ]

    def verify_selectable(self, obligations: list[ProofObligation]) -> bool:
        for obligation in obligations:
            if obligation.status == ProofObligationStatus.PROVEN:
                continue
            if obligation.status == ProofObligationStatus.NOT_APPLICABLE and obligation.justification:
                continue
            raise ProofObligationError(
                f"proof obligation {obligation.claim_type.value} is {obligation.status.value}"
            )
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_proof_obligations.py -v
```

Expected: PASS, 4 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/proof_obligation.py src/de_forge/services/proof_obligation_service.py tests/unit/services/test_proof_obligations.py
git commit -m "feat(proof): add proof obligation gates"
```

---

### Task 9: Full foundation verification

**Files:**
- Modify only if previous tasks revealed import/package issues.

- [ ] **Step 1: Run all foundation tests**

Run:

```bash
pytest tests/unit/core tests/unit/services tests/integration/db -v --cov=src --cov-report=term-missing
```

Expected: PASS for all tests added by this plan.

- [ ] **Step 2: Run type checking**

Run:

```bash
mypy src/
```

Expected: PASS. If mypy flags SQLAlchemy mapped JSON types, fix by using explicit `Mapped[...]` annotations already shown in this plan.

- [ ] **Step 3: Run linting**

Run:

```bash
ruff check src/ tests/
```

Expected: PASS.

- [ ] **Step 4: Run formatting check**

Run:

```bash
ruff format --check src/ tests/
```

Expected: PASS.

- [ ] **Step 5: Commit verification fixes if any**

If Steps 1-4 required fixes, commit only the fix files:

```bash
git add <fixed-files>
git commit -m "test: verify SOTA Core v2 foundation gates"
```

If no fixes were needed, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this foundation plan:

- Stable hashing/idempotency: Task 1.
- Artifact lineage and DB foundation: Tasks 2-3.
- Evidence graph primitives: Task 4.
- Deterministic chunking and citation verification: Task 5.
- ATT&CK Detection Strategy / Analytic / Data Component modeling: Task 6.
- Multi-platform telemetry registry: Task 6.
- Formal DetectionSpec verification: Task 7.
- Proof obligations: Task 8.
- Full verification: Task 9.

Deferred to later plans because they depend on this foundation:

- LLM client and controlled agents.
- Detection AST and Sigma compiler.
- Rule portfolio generation.
- Static Sigma validation.
- Dynamic/adversarial/counterfactual evaluation.
- Oracle evaluation.
- Orchestrator modes.
- Web UI.
- Feedback learning and Detection CI/CD regression execution.
- Quality dashboard and CTI-REALM adapter.

No placeholder tasks are intentionally left in this plan. Each task includes files, test code, implementation code, commands, expected results, and commit boundaries.
