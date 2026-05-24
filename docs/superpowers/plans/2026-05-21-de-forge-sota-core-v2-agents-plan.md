# DE-Forge SOTA Core v2 Controlled Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add controlled LLM-backed agents with strict schemas, prompt versioning, audit persistence, citation verification, and validator gates.

**Architecture:** Agents are not trusted decision makers. Each agent receives strict input, returns strict JSON, is schema-validated, audited, and routed through deterministic gates before its output can enter the evidence graph, DetectionSpec, AST, or rule candidate layers.

**Tech Stack:** Python 3.11+, OpenAI-compatible API via httpx or OpenAI SDK, Pydantic v2, SQLAlchemy, pytest, ruff, mypy.

> **Commit policy:** Commit steps in this plan are conditional. Execute them only if the user explicitly authorizes commits for the current execution session. Otherwise skip commit commands and report changed files per task.

---

## Prerequisites

This plan starts after these plans pass:

- Foundation plan.
- Compiler plan.
- Validation/oracle/regression plan.

Required existing files:

- `src/de_forge/services/citation_verifier.py`
- `src/de_forge/services/evidence_graph.py`
- `src/de_forge/services/detection_spec_verifier.py`
- `src/de_forge/services/telemetry_registry.py`

## File structure map

- `src/de_forge/schemas/agent_io.py` — standard agent input/output envelope.
- `src/de_forge/models/agent_run.py` — persisted agent run audit.
- `src/de_forge/services/llm_client.py` — OpenAI-compatible client wrapper.
- `src/de_forge/services/prompt_registry.py` — versioned prompt registry.
- `src/de_forge/services/agent_audit.py` — persist agent inputs/outputs/hashes.
- `src/de_forge/agents/base.py` — base agent runner and output validation.
- `src/de_forge/agents/evidence_agent.py` — evidence extraction contract.
- `src/de_forge/agents/attack_mapping_agent.py` — ATT&CK mapping contract.
- `src/de_forge/agents/detection_spec_agent.py` — DetectionSpec construction contract.
- `src/de_forge/agents/critic_agent.py` — critic findings contract.
- `tests/unit/agents/test_agent_contracts.py`
- `tests/integration/agents/test_agent_audit.py`

---

### Task 1: Agent IO envelope schemas

**Files:**
- Create: `src/de_forge/schemas/agent_io.py`
- Test: `tests/unit/agents/test_agent_contracts.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/agents/test_agent_contracts.py`:

```python
import pytest
from pydantic import ValidationError

from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope, Citation


def test_agent_output_envelope_tracks_metadata_and_artifacts() -> None:
    output = AgentOutputEnvelope(
        run_id="run_1",
        agent_name="evidence_agent",
        input_artifact_ids=["artifact_1"],
        output={"evidence_quotes": []},
        confidence=0.9,
        citations=[],
        abstain=False,
        abstain_reason=None,
        metadata=AgentMetadata(
            model="cx/gpt-5.5",
            prompt_version="evidence:v1",
            tokens_in=100,
            tokens_out=50,
            latency_ms=1000,
        ),
    )

    assert output.agent_name == "evidence_agent"
    assert output.metadata.model == "cx/gpt-5.5"


def test_agent_output_confidence_must_be_bounded() -> None:
    with pytest.raises(ValidationError):
        AgentOutputEnvelope(
            run_id="run_1",
            agent_name="bad_agent",
            input_artifact_ids=[],
            output={},
            confidence=1.5,
            citations=[],
            abstain=False,
            metadata=AgentMetadata(model="m", prompt_version="p", tokens_in=0, tokens_out=0, latency_ms=0),
        )


def test_citation_schema_tracks_exact_span() -> None:
    citation = Citation(chunk_id="chunk_1", quote="encoded command", start_offset=10, end_offset=25)

    assert citation.chunk_id == "chunk_1"
    assert citation.start_offset == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: FAIL with import error for `de_forge.schemas.agent_io`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/agent_io.py`:

```python
"""Standard contracts for controlled agent IO."""

from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: str
    quote: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)


class AgentMetadata(BaseModel):
    model: str
    prompt_version: str
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0)


class AgentOutputEnvelope(BaseModel):
    run_id: str
    agent_name: str
    input_artifact_ids: list[str]
    output: dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)
    abstain: bool = False
    abstain_reason: str | None = None
    metadata: AgentMetadata
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/agent_io.py tests/unit/agents/test_agent_contracts.py
git commit -m "feat(agents): add controlled agent IO envelope"
```

---

### Task 2: Prompt registry and LLM client interface

**Files:**
- Create: `src/de_forge/services/prompt_registry.py`
- Create: `src/de_forge/services/llm_client.py`
- Modify: `tests/unit/agents/test_agent_contracts.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/agents/test_agent_contracts.py`:

```python
from de_forge.services.llm_client import LlmRequest, LlmResponse
from de_forge.services.prompt_registry import PromptRegistry


def test_prompt_registry_returns_versioned_prompt() -> None:
    registry = PromptRegistry.default()

    prompt = registry.get("evidence_agent", "v1")

    assert prompt.prompt_id == "evidence_agent:v1"
    assert "Extract only explicitly supported behavioral evidence" in prompt.system_prompt


def test_llm_request_and_response_contracts() -> None:
    request = LlmRequest(system_prompt="system", user_prompt="user", response_schema_name="EvidenceOutput")
    response = LlmResponse(content={"ok": True}, tokens_in=10, tokens_out=5, latency_ms=20)

    assert request.response_schema_name == "EvidenceOutput"
    assert response.content == {"ok": True}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py::test_prompt_registry_returns_versioned_prompt -v
```

Expected: FAIL with import error for prompt registry.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/prompt_registry.py`:

```python
"""Versioned prompt registry for controlled agents."""

from pydantic import BaseModel


class PromptDefinition(BaseModel):
    prompt_id: str
    agent_name: str
    version: str
    system_prompt: str


class PromptRegistry:
    """In-memory prompt registry for initial agent implementation."""

    def __init__(self, prompts: list[PromptDefinition]) -> None:
        self.prompts = {(prompt.agent_name, prompt.version): prompt for prompt in prompts}

    @classmethod
    def default(cls) -> "PromptRegistry":
        return cls(
            prompts=[
                PromptDefinition(
                    prompt_id="evidence_agent:v1",
                    agent_name="evidence_agent",
                    version="v1",
                    system_prompt="Extract only explicitly supported behavioral evidence from provided chunks. Return strict JSON only.",
                ),
                PromptDefinition(
                    prompt_id="attack_mapping_agent:v1",
                    agent_name="attack_mapping_agent",
                    version="v1",
                    system_prompt="Map extracted behaviors to ATT&CK techniques using only supplied evidence. Return strict JSON only.",
                ),
            ]
        )

    def get(self, agent_name: str, version: str) -> PromptDefinition:
        return self.prompts[(agent_name, version)]
```

Create `src/de_forge/services/llm_client.py`:

```python
"""OpenAI-compatible LLM client contracts."""

from typing import Any

from pydantic import BaseModel, Field


class LlmRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    response_schema_name: str


class LlmResponse(BaseModel):
    content: dict[str, Any]
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0)


class LlmClient:
    """Interface for OpenAI-compatible LLM calls."""

    def complete_json(self, request: LlmRequest) -> LlmResponse:
        raise NotImplementedError("LLM transport is implemented in the integration task")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/prompt_registry.py src/de_forge/services/llm_client.py tests/unit/agents/test_agent_contracts.py
git commit -m "feat(agents): add prompt registry and LLM contracts"
```

---

### Task 3: Agent audit persistence

**Files:**
- Create: `src/de_forge/models/agent_run.py`
- Create: `src/de_forge/services/agent_audit.py`
- Test: `tests/integration/agents/test_agent_audit.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/agents/test_agent_audit.py`:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from de_forge.db.base import Base
from de_forge.models.agent_run import AgentRun
from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope
from de_forge.services.agent_audit import AgentAuditService


def test_agent_audit_persists_input_output_hashes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    envelope = AgentOutputEnvelope(
        run_id="run_1",
        agent_name="evidence_agent",
        input_artifact_ids=["artifact_1"],
        output={"evidence_quotes": []},
        confidence=0.9,
        citations=[],
        abstain=False,
        metadata=AgentMetadata(model="cx/gpt-5.5", prompt_version="evidence_agent:v1", tokens_in=10, tokens_out=5, latency_ms=100),
    )

    with Session(engine) as session:
        record = AgentAuditService(session).persist(input_payload={"chunks": []}, output_envelope=envelope)
        session.commit()
        loaded = session.scalar(select(AgentRun).where(AgentRun.id == record.id))

    assert loaded is not None
    assert loaded.agent_name == "evidence_agent"
    assert loaded.input_hash
    assert loaded.output_hash
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/agents/test_agent_audit.py -v
```

Expected: FAIL with import error for `de_forge.models.agent_run`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/models/agent_run.py`:

```python
"""Agent run audit persistence."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from de_forge.db.base import Base


class AgentRun(Base):
    """Persisted audit record for a controlled agent run."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"agent_run_{uuid.uuid4().hex}")
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    input_hash: Mapped[str] = mapped_column(String, nullable=False)
    output_hash: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    terminal_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

Create `src/de_forge/services/agent_audit.py`:

```python
"""Persist agent run audit records."""

from typing import Any

from sqlalchemy.orm import Session

from de_forge.core.hashing import snapshot_hash
from de_forge.models.agent_run import AgentRun
from de_forge.schemas.agent_io import AgentOutputEnvelope


class AgentAuditService:
    """Persist agent input/output snapshots and metadata."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def persist(self, input_payload: dict[str, Any], output_envelope: AgentOutputEnvelope) -> AgentRun:
        output_payload = output_envelope.model_dump()
        record = AgentRun(
            run_id=output_envelope.run_id,
            agent_name=output_envelope.agent_name,
            input_payload=input_payload,
            output_payload=output_payload,
            input_hash=snapshot_hash(input_payload),
            output_hash=snapshot_hash(output_payload),
            model=output_envelope.metadata.model,
            prompt_version=output_envelope.metadata.prompt_version,
            tokens_in=output_envelope.metadata.tokens_in,
            tokens_out=output_envelope.metadata.tokens_out,
            latency_ms=output_envelope.metadata.latency_ms,
            cost_usd=output_envelope.metadata.cost_usd,
            terminal_status="abstain" if output_envelope.abstain else "success",
        )
        self.session.add(record)
        self.session.flush()
        return record
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/agents/test_agent_audit.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/models/agent_run.py src/de_forge/services/agent_audit.py tests/integration/agents/test_agent_audit.py
git commit -m "feat(agents): persist agent run audit records"
```

---

### Task 4: Base agent runner with schema validation

**Files:**
- Create: `src/de_forge/agents/base.py`
- Modify: `tests/unit/agents/test_agent_contracts.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/agents/test_agent_contracts.py`:

```python
from de_forge.agents.base import BaseAgent
from de_forge.services.llm_client import LlmClient, LlmRequest, LlmResponse


class FakeClient(LlmClient):
    def complete_json(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(content={"answer": "ok"}, tokens_in=1, tokens_out=1, latency_ms=1)


class TestAgent(BaseAgent):
    agent_name = "test_agent"
    prompt_version = "v1"
    response_schema_name = "TestOutput"

    def build_user_prompt(self, input_payload: dict[str, object]) -> str:
        return "test"


def test_base_agent_wraps_llm_response_in_envelope() -> None:
    agent = TestAgent(llm_client=FakeClient(), system_prompt="system")

    envelope = agent.run(run_id="run_1", input_artifact_ids=["artifact_1"], input_payload={"x": 1})

    assert envelope.agent_name == "test_agent"
    assert envelope.output == {"answer": "ok"}
    assert envelope.metadata.prompt_version == "test_agent:v1"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py::test_base_agent_wraps_llm_response_in_envelope -v
```

Expected: FAIL with import error for `de_forge.agents.base`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/agents/base.py`:

```python
"""Base class for controlled LLM agents."""

from abc import ABC, abstractmethod
from typing import Any

from de_forge.core.config import settings
from de_forge.schemas.agent_io import AgentMetadata, AgentOutputEnvelope
from de_forge.services.llm_client import LlmClient, LlmRequest


class BaseAgent(ABC):
    """Run an agent through strict request/response envelopes."""

    agent_name: str
    prompt_version: str
    response_schema_name: str

    def __init__(self, llm_client: LlmClient, system_prompt: str) -> None:
        self.llm_client = llm_client
        self.system_prompt = system_prompt

    def run(
        self,
        run_id: str,
        input_artifact_ids: list[str],
        input_payload: dict[str, Any],
    ) -> AgentOutputEnvelope:
        request = LlmRequest(
            system_prompt=self.system_prompt,
            user_prompt=self.build_user_prompt(input_payload),
            response_schema_name=self.response_schema_name,
        )
        response = self.llm_client.complete_json(request)
        return AgentOutputEnvelope(
            run_id=run_id,
            agent_name=self.agent_name,
            input_artifact_ids=input_artifact_ids,
            output=response.content,
            confidence=float(response.content.get("confidence", 1.0)),
            citations=[],
            abstain=bool(response.content.get("abstain", False)),
            abstain_reason=response.content.get("abstain_reason"),
            metadata=AgentMetadata(
                model=settings.openai_model,
                prompt_version=f"{self.agent_name}:{self.prompt_version}",
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
                latency_ms=response.latency_ms,
                cost_usd=response.cost_usd,
            ),
        )

    @abstractmethod
    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        """Build the user prompt from structured input payload."""
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/agents/base.py tests/unit/agents/test_agent_contracts.py
git commit -m "feat(agents): add controlled base agent runner"
```

---

### Task 5: Evidence agent contract with citation extraction

**Files:**
- Create: `src/de_forge/agents/evidence_agent.py`
- Modify: `tests/unit/agents/test_agent_contracts.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/agents/test_agent_contracts.py`:

```python
from de_forge.agents.evidence_agent import EvidenceAgent


class EvidenceFakeClient(LlmClient):
    def complete_json(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(
            content={
                "confidence": 0.95,
                "evidence_quotes": [
                    {
                        "quote": "PowerShell executed an encoded command",
                        "chunk_id": "chunk_1",
                        "start_offset": 0,
                        "end_offset": 38,
                        "behavior_label": "encoded PowerShell execution",
                    }
                ],
                "abstain": False,
            },
            tokens_in=20,
            tokens_out=10,
            latency_ms=50,
        )


def test_evidence_agent_returns_citations_from_evidence_quotes() -> None:
    agent = EvidenceAgent(llm_client=EvidenceFakeClient())

    envelope = agent.run(
        run_id="run_1",
        input_artifact_ids=["chunk_artifact_1"],
        input_payload={"chunks": [{"id": "chunk_1", "text": "PowerShell executed an encoded command"}]},
    )

    assert envelope.agent_name == "evidence_agent"
    assert envelope.citations[0].chunk_id == "chunk_1"
    assert envelope.citations[0].quote == "PowerShell executed an encoded command"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py::test_evidence_agent_returns_citations_from_evidence_quotes -v
```

Expected: FAIL with import error for evidence agent.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/agents/evidence_agent.py`:

```python
"""Evidence extraction agent contract."""

from typing import Any

from de_forge.agents.base import BaseAgent
from de_forge.schemas.agent_io import AgentOutputEnvelope, Citation
from de_forge.services.llm_client import LlmClient
from de_forge.services.prompt_registry import PromptRegistry


class EvidenceAgent(BaseAgent):
    """Extract evidence quotes with exact chunk citations."""

    agent_name = "evidence_agent"
    prompt_version = "v1"
    response_schema_name = "EvidenceOutput"

    def __init__(self, llm_client: LlmClient) -> None:
        prompt = PromptRegistry.default().get(self.agent_name, self.prompt_version)
        super().__init__(llm_client=llm_client, system_prompt=prompt.system_prompt)

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Extract evidence from chunks: {input_payload['chunks']}"

    def run(self, run_id: str, input_artifact_ids: list[str], input_payload: dict[str, Any]) -> AgentOutputEnvelope:
        envelope = super().run(run_id, input_artifact_ids, input_payload)
        citations = [
            Citation(
                chunk_id=item["chunk_id"],
                quote=item["quote"],
                start_offset=item["start_offset"],
                end_offset=item["end_offset"],
            )
            for item in envelope.output.get("evidence_quotes", [])
        ]
        return envelope.model_copy(update={"citations": citations})
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/agents/evidence_agent.py tests/unit/agents/test_agent_contracts.py
git commit -m "feat(agents): add evidence agent citation contract"
```

---

### Task 6: ATT&CK mapping, DetectionSpec, and Critic agent contracts

**Files:**
- Create: `src/de_forge/agents/attack_mapping_agent.py`
- Create: `src/de_forge/agents/detection_spec_agent.py`
- Create: `src/de_forge/agents/critic_agent.py`
- Modify: `tests/unit/agents/test_agent_contracts.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/agents/test_agent_contracts.py`:

```python
from de_forge.agents.attack_mapping_agent import AttackMappingAgent
from de_forge.agents.critic_agent import CriticAgent
from de_forge.agents.detection_spec_agent import DetectionSpecAgent


def test_attack_mapping_agent_prompt_mentions_evidence_only() -> None:
    agent = AttackMappingAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"behaviors": [{"id": "behavior_1"}], "evidence": []})

    assert "using only supplied evidence" in prompt


def test_detection_spec_agent_prompt_mentions_verified_spec_contract() -> None:
    agent = DetectionSpecAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"graph_paths": []})

    assert "DetectionSpec" in prompt
    assert "telemetry" in prompt


def test_critic_agent_prompt_asks_for_false_positive_and_bypass_risks() -> None:
    agent = CriticAgent(llm_client=FakeClient())

    prompt = agent.build_user_prompt({"candidate": {"id": "candidate_1"}})

    assert "false positive" in prompt
    assert "bypass" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py::test_attack_mapping_agent_prompt_mentions_evidence_only -v
```

Expected: FAIL with import error for attack mapping agent.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/agents/attack_mapping_agent.py`:

```python
"""ATT&CK mapping agent contract."""

from typing import Any

from de_forge.agents.base import BaseAgent
from de_forge.services.llm_client import LlmClient


class AttackMappingAgent(BaseAgent):
    agent_name = "attack_mapping_agent"
    prompt_version = "v1"
    response_schema_name = "AttackMappingOutput"

    def __init__(self, llm_client: LlmClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt="Map behaviors to ATT&CK techniques using strict JSON.")

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Map behaviors to ATT&CK techniques using only supplied evidence: {input_payload}"
```

Create `src/de_forge/agents/detection_spec_agent.py`:

```python
"""DetectionSpec construction agent contract."""

from typing import Any

from de_forge.agents.base import BaseAgent
from de_forge.services.llm_client import LlmClient


class DetectionSpecAgent(BaseAgent):
    agent_name = "detection_spec_agent"
    prompt_version = "v1"
    response_schema_name = "DetectionSpecOutput"

    def __init__(self, llm_client: LlmClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt="Build verified DetectionSpec JSON from graph paths.")

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Build a DetectionSpec with evidence, ATT&CK, telemetry, allowed fields, logic, false positives, and test plan: {input_payload}"
```

Create `src/de_forge/agents/critic_agent.py`:

```python
"""Detection critic agent contract."""

from typing import Any

from de_forge.agents.base import BaseAgent
from de_forge.services.llm_client import LlmClient


class CriticAgent(BaseAgent):
    agent_name = "critic_agent"
    prompt_version = "v1"
    response_schema_name = "CriticOutput"

    def __init__(self, llm_client: LlmClient) -> None:
        super().__init__(llm_client=llm_client, system_prompt="Critique rule candidates for detection engineering risks.")

    def build_user_prompt(self, input_payload: dict[str, Any]) -> str:
        return f"Review candidate for false positive risk, false negative risk, bypass risk, telemetry gaps, and unsupported claims: {input_payload}"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/agents/test_agent_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/agents/attack_mapping_agent.py src/de_forge/agents/detection_spec_agent.py src/de_forge/agents/critic_agent.py tests/unit/agents/test_agent_contracts.py
git commit -m "feat(agents): add mapping spec and critic agent contracts"
```

---

### Task 7: Full agents verification

**Files:**
- Modify only if verification finds issues.

- [ ] **Step 1: Run agent tests**

Run:

```bash
pytest tests/unit/agents tests/integration/agents -v
```

Expected: PASS.

- [ ] **Step 2: Run all unit and integration tests**

Run:

```bash
pytest tests/ -v
```

Expected: PASS.

- [ ] **Step 3: Run type checking**

Run:

```bash
mypy src/
```

Expected: PASS.

- [ ] **Step 4: Run linting and formatting check**

Run:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

Expected: PASS.

- [ ] **Step 5: Commit verification fixes if needed**

If fixes were required:

```bash
git add <fixed-files>
git commit -m "test: verify controlled agent contracts"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this agents plan:

- Agent IO envelope: Task 1.
- Prompt registry and LLM contracts: Task 2.
- Agent audit persistence: Task 3.
- Base controlled runner: Task 4.
- Evidence citation agent contract: Task 5.
- ATT&CK, DetectionSpec, critic contracts: Task 6.

Deferred to orchestrator plan:

- Full pipeline stage wiring.
- Agent output insertion into evidence graph.
- Runtime citation verification against chunk storage.
- Auto/cautious mode behavior.
