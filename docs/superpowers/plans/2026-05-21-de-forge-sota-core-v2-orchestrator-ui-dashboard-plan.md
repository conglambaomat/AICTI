# DE-Forge SOTA Core v2 Orchestrator, UI, and Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement end-to-end orchestration, auto/cautious execution modes, API routes, minimal trust-oriented Web UI support, and quality dashboard data for DE-Forge SOTA Core v2.

**Architecture:** The orchestrator owns state transitions and hard gates. API routes are thin wrappers over services. The initial UI can be server-rendered/API-driven, but must expose evidence -> graph -> DetectionSpec -> proof -> rule -> validation -> review lineage so the user can trust and review final candidates.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, pytest, httpx, ruff, mypy. Frontend can initially use FastAPI JSON endpoints and simple server-rendered HTML or a later dedicated frontend plan.

> **Commit policy:** Commit steps in this plan are conditional. Execute them only if the user explicitly authorizes commits for the current execution session. Otherwise skip commit commands and report changed files per task.

---

## Prerequisites

This plan starts after these plans pass:

- Foundation plan.
- Compiler plan.
- Validation/oracle/regression plan.
- Controlled agents plan.

Required existing files:

- `src/de_forge/main.py`
- `src/de_forge/services/*` from earlier plans.
- `src/de_forge/schemas/*` from earlier plans.

## File structure map

- `src/de_forge/schemas/run.py` — run state and mode schemas.
- `src/de_forge/schemas/review.py` — review request/decision schemas.
- `src/de_forge/services/state_machine.py` — allowed state transitions.
- `src/de_forge/services/gates.py` — hard gate predicates.
- `src/de_forge/services/orchestrator.py` — golden-path orchestration.
- `src/de_forge/services/review.py` — review decision handling.
- `src/de_forge/services/metrics.py` — quality dashboard snapshots.
- `src/de_forge/api/routes/reports.py` — report upload/list endpoints.
- `src/de_forge/api/routes/runs.py` — start/inspect run endpoints.
- `src/de_forge/api/routes/review.py` — human review endpoints.
- `src/de_forge/api/routes/metrics.py` — dashboard metric endpoints.
- `src/de_forge/api/router.py` — route aggregation.
- Modify: `src/de_forge/main.py` — include API router.
- `tests/unit/services/test_state_machine_gates.py`
- `tests/integration/services/test_orchestrator_golden_path.py`
- `tests/integration/api/test_api_routes.py`
- `tests/unit/services/test_metrics.py`

---

### Task 1: Run schemas and state machine

**Files:**
- Create: `src/de_forge/schemas/run.py`
- Create: `src/de_forge/services/state_machine.py`
- Test: `tests/unit/services/test_state_machine_gates.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_state_machine_gates.py`:

```python
import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.state_machine import StateMachine


def test_state_machine_allows_ingestion_to_evidence_transition() -> None:
    machine = StateMachine()

    assert machine.transition(RunState.INGESTED, RunState.EVIDENCE_READY) == RunState.EVIDENCE_READY


def test_state_machine_rejects_raw_report_to_rule_candidate_transition() -> None:
    machine = StateMachine()

    with pytest.raises(ValidationGateError):
        machine.transition(RunState.INGESTED, RunState.RULE_CANDIDATES_READY)


def test_run_mode_values_include_auto_and_cautious() -> None:
    assert RunMode.AUTO == "auto"
    assert RunMode.CAUTIOUS == "cautious"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py -v
```

Expected: FAIL with import error for `de_forge.schemas.run`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/run.py`:

```python
"""Run modes and states for orchestrated pipeline execution."""

from enum import StrEnum

from pydantic import BaseModel


class RunMode(StrEnum):
    AUTO = "auto"
    CAUTIOUS = "cautious"


class RunState(StrEnum):
    CREATED = "created"
    INGESTED = "ingested"
    EVIDENCE_READY = "evidence_ready"
    DETECTION_SPEC_READY = "detection_spec_ready"
    DETECTION_SPEC_VERIFIED = "detection_spec_verified"
    RULE_CANDIDATES_READY = "rule_candidates_ready"
    VALIDATED = "validated"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ABSTAINED = "abstained"
    FAILED = "failed"


class RunSummary(BaseModel):
    id: str
    mode: RunMode
    state: RunState
    report_id: str
```

Create `src/de_forge/services/state_machine.py`:

```python
"""Pipeline state transition rules."""

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.run import RunState


class StateMachine:
    """Enforce legal run state transitions."""

    def __init__(self) -> None:
        self.allowed = {
            RunState.CREATED: {RunState.INGESTED, RunState.FAILED},
            RunState.INGESTED: {RunState.EVIDENCE_READY, RunState.ABSTAINED, RunState.FAILED},
            RunState.EVIDENCE_READY: {RunState.DETECTION_SPEC_READY, RunState.ABSTAINED, RunState.FAILED},
            RunState.DETECTION_SPEC_READY: {RunState.DETECTION_SPEC_VERIFIED, RunState.AWAITING_REVIEW, RunState.FAILED},
            RunState.DETECTION_SPEC_VERIFIED: {RunState.RULE_CANDIDATES_READY, RunState.ABSTAINED, RunState.FAILED},
            RunState.RULE_CANDIDATES_READY: {RunState.VALIDATED, RunState.ABSTAINED, RunState.FAILED},
            RunState.VALIDATED: {RunState.AWAITING_REVIEW, RunState.ABSTAINED, RunState.FAILED},
            RunState.AWAITING_REVIEW: {RunState.APPROVED, RunState.REJECTED},
        }

    def transition(self, current: RunState, target: RunState) -> RunState:
        if target not in self.allowed.get(current, set()):
            raise ValidationGateError(f"illegal transition from {current.value} to {target.value}")
        return target
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/run.py src/de_forge/services/state_machine.py tests/unit/services/test_state_machine_gates.py
git commit -m "feat(orchestration): add run states and transition rules"
```

---

### Task 2: Gate predicates

**Files:**
- Create: `src/de_forge/services/gates.py`
- Modify: `tests/unit/services/test_state_machine_gates.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/services/test_state_machine_gates.py`:

```python
from de_forge.schemas.proof_obligation import ProofObligation, ProofObligationStatus, ProofObligationType
from de_forge.services.gates import can_enter_final_review, can_generate_rule


def test_can_generate_rule_requires_verified_detection_spec() -> None:
    assert can_generate_rule(detection_spec_verified=True) is True
    assert can_generate_rule(detection_spec_verified=False) is False


def test_can_enter_final_review_requires_proven_obligations_and_validation() -> None:
    obligations = [
        ProofObligation(
            run_id="run_1",
            rule_candidate_id="candidate_1",
            claim_type=ProofObligationType.CITATION_FAITHFUL,
            claim_text="citations exact",
            required_artifact_types=["citation_verification"],
            status=ProofObligationStatus.PROVEN,
        )
    ]

    assert can_enter_final_review(static_valid=True, proof_obligations=obligations) is True
    assert can_enter_final_review(static_valid=False, proof_obligations=obligations) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py::test_can_generate_rule_requires_verified_detection_spec -v
```

Expected: FAIL with import error for gates service.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/gates.py`:

```python
"""Hard gate predicates for orchestration."""

from de_forge.schemas.proof_obligation import ProofObligation, ProofObligationStatus


def can_generate_rule(detection_spec_verified: bool) -> bool:
    """Return whether rule generation may start."""
    return detection_spec_verified


def can_enter_final_review(static_valid: bool, proof_obligations: list[ProofObligation]) -> bool:
    """Return whether a candidate may enter human review."""
    if not static_valid:
        return False
    return all(obligation.status == ProofObligationStatus.PROVEN for obligation in proof_obligations)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/gates.py tests/unit/services/test_state_machine_gates.py
git commit -m "feat(orchestration): add hard gate predicates"
```

---

### Task 3: Golden-path orchestrator skeleton

**Files:**
- Create: `src/de_forge/services/orchestrator.py`
- Test: `tests/integration/services/test_orchestrator_golden_path.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/services/test_orchestrator_golden_path.py`:

```python
from de_forge.schemas.run import RunMode, RunState
from de_forge.services.orchestrator import Orchestrator


def test_orchestrator_auto_mode_reaches_awaiting_review_for_golden_path() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report_1",
        report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        mode=RunMode.AUTO,
    )

    assert result.state == RunState.AWAITING_REVIEW
    assert result.report_id == "report_1"


def test_orchestrator_cautious_mode_pauses_at_detection_spec() -> None:
    orchestrator = Orchestrator()

    result = orchestrator.run_golden_path(
        report_id="report_1",
        report_text="PowerShell executed an encoded command using powershell.exe -enc AAA.",
        mode=RunMode.CAUTIOUS,
    )

    assert result.state == RunState.DETECTION_SPEC_READY
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/services/test_orchestrator_golden_path.py -v
```

Expected: FAIL with import error for orchestrator.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/orchestrator.py`:

```python
"""Initial end-to-end orchestrator for the golden path."""

from de_forge.schemas.run import RunMode, RunState, RunSummary
from de_forge.services.state_machine import StateMachine


class Orchestrator:
    """Coordinate pipeline stages through hard-gated state transitions."""

    def __init__(self) -> None:
        self.state_machine = StateMachine()

    def run_golden_path(self, report_id: str, report_text: str, mode: RunMode) -> RunSummary:
        del report_text
        state = RunState.CREATED
        state = self.state_machine.transition(state, RunState.INGESTED)
        state = self.state_machine.transition(state, RunState.EVIDENCE_READY)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_READY)
        if mode == RunMode.CAUTIOUS:
            return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_VERIFIED)
        state = self.state_machine.transition(state, RunState.RULE_CANDIDATES_READY)
        state = self.state_machine.transition(state, RunState.VALIDATED)
        state = self.state_machine.transition(state, RunState.AWAITING_REVIEW)
        return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/services/test_orchestrator_golden_path.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/orchestrator.py tests/integration/services/test_orchestrator_golden_path.py
git commit -m "feat(orchestration): add golden-path orchestrator skeleton"
```

---

### Task 4: Review schemas and service

**Files:**
- Create: `src/de_forge/schemas/review.py`
- Create: `src/de_forge/services/review.py`
- Test: `tests/unit/services/test_review_service.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_review_service.py`:

```python
from de_forge.schemas.review import ReviewAction, ReviewRequest
from de_forge.services.review import ReviewService


def test_review_service_records_approval_decision() -> None:
    request = ReviewRequest(
        run_id="run_1",
        rule_candidate_id="candidate_1",
        action=ReviewAction.APPROVE,
        reviewer_notes="Looks good",
    )

    decision = ReviewService().decide(request)

    assert decision.action == ReviewAction.APPROVE
    assert decision.export_allowed is True


def test_review_service_blocks_export_on_reject() -> None:
    request = ReviewRequest(
        run_id="run_1",
        rule_candidate_id="candidate_1",
        action=ReviewAction.REJECT,
        reviewer_notes="Too broad",
    )

    decision = ReviewService().decide(request)

    assert decision.export_allowed is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_review_service.py -v
```

Expected: FAIL with import error for review schema.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/review.py`:

```python
"""Human review contracts."""

from enum import StrEnum

from pydantic import BaseModel


class ReviewAction(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    EDIT = "edit"
    ABSTAIN = "abstain"


class ReviewRequest(BaseModel):
    run_id: str
    rule_candidate_id: str
    action: ReviewAction
    reviewer_notes: str


class ReviewDecision(BaseModel):
    run_id: str
    rule_candidate_id: str
    action: ReviewAction
    reviewer_notes: str
    export_allowed: bool
```

Create `src/de_forge/services/review.py`:

```python
"""Human review decision service."""

from de_forge.schemas.review import ReviewAction, ReviewDecision, ReviewRequest


class ReviewService:
    """Apply human review decision and export policy."""

    def decide(self, request: ReviewRequest) -> ReviewDecision:
        export_allowed = request.action == ReviewAction.APPROVE
        return ReviewDecision(
            run_id=request.run_id,
            rule_candidate_id=request.rule_candidate_id,
            action=request.action,
            reviewer_notes=request.reviewer_notes,
            export_allowed=export_allowed,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_review_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/review.py src/de_forge/services/review.py tests/unit/services/test_review_service.py
git commit -m "feat(review): add human review decision service"
```

---

### Task 5: API router for runs and review

**Files:**
- Create: `src/de_forge/api/router.py`
- Create: `src/de_forge/api/routes/runs.py`
- Create: `src/de_forge/api/routes/review.py`
- Modify: `src/de_forge/main.py`
- Test: `tests/integration/api/test_api_routes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/integration/api/test_api_routes.py`:

```python
from fastapi.testclient import TestClient

from de_forge.main import app


def test_start_golden_run_endpoint_returns_awaiting_review() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/runs/golden",
        json={"report_id": "report_1", "report_text": "PowerShell -enc AAA", "mode": "auto"},
    )

    assert response.status_code == 200
    assert response.json()["state"] == "awaiting_review"


def test_review_endpoint_blocks_export_on_reject() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/review",
        json={"run_id": "run_1", "rule_candidate_id": "candidate_1", "action": "reject", "reviewer_notes": "Too broad"},
    )

    assert response.status_code == 200
    assert response.json()["export_allowed"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/api/test_api_routes.py -v
```

Expected: FAIL with 404 for new API routes.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/api/routes/runs.py`:

```python
"""Run orchestration API routes."""

from pydantic import BaseModel
from fastapi import APIRouter

from de_forge.schemas.run import RunMode, RunSummary
from de_forge.services.orchestrator import Orchestrator

router = APIRouter(prefix="/runs", tags=["runs"])


class GoldenRunRequest(BaseModel):
    report_id: str
    report_text: str
    mode: RunMode


@router.post("/golden", response_model=RunSummary)
def start_golden_run(request: GoldenRunRequest) -> RunSummary:
    return Orchestrator().run_golden_path(request.report_id, request.report_text, request.mode)
```

Create `src/de_forge/api/routes/review.py`:

```python
"""Human review API routes."""

from fastapi import APIRouter

from de_forge.schemas.review import ReviewDecision, ReviewRequest
from de_forge.services.review import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


@router.post("", response_model=ReviewDecision)
def submit_review(request: ReviewRequest) -> ReviewDecision:
    return ReviewService().decide(request)
```

Create `src/de_forge/api/router.py`:

```python
"""Aggregate API router."""

from fastapi import APIRouter

from de_forge.api.routes import review, runs

api_router = APIRouter(prefix="/api")
api_router.include_router(runs.router)
api_router.include_router(review.router)
```

Modify `src/de_forge/main.py` to import and include router:

```python
from de_forge.api.router import api_router
```

Add after middleware:

```python
app.include_router(api_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/api src/de_forge/main.py tests/integration/api/test_api_routes.py
git commit -m "feat(api): add run and review endpoints"
```

---

### Task 6: Metrics snapshots for dashboard

**Files:**
- Create: `src/de_forge/services/metrics.py`
- Create: `src/de_forge/api/routes/metrics.py`
- Modify: `src/de_forge/api/router.py`
- Test: `tests/unit/services/test_metrics.py`
- Modify: `tests/integration/api/test_api_routes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_metrics.py`:

```python
from de_forge.services.metrics import MetricsService


def test_metrics_service_summarizes_quality_snapshot() -> None:
    summary = MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=0.9,
        static_validity_rate=0.95,
        regression_pass_rate=1.0,
    )

    assert summary["citation_faithfulness"] == 1.0
    assert summary["overall_quality"] == 0.9625
```

Append to `tests/integration/api/test_api_routes.py`:

```python

def test_metrics_endpoint_returns_quality_summary() -> None:
    client = TestClient(app)

    response = client.get("/api/metrics/quality")

    assert response.status_code == 200
    assert "overall_quality" in response.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_metrics.py tests/integration/api/test_api_routes.py::test_metrics_endpoint_returns_quality_summary -v
```

Expected: FAIL with import error or 404 metrics route.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/metrics.py`:

```python
"""Quality metric summaries for dashboard views."""


class MetricsService:
    """Compute quality snapshot summaries."""

    def quality_snapshot(
        self,
        citation_faithfulness: float,
        proof_pass_rate: float,
        static_validity_rate: float,
        regression_pass_rate: float,
    ) -> dict[str, float]:
        values = [citation_faithfulness, proof_pass_rate, static_validity_rate, regression_pass_rate]
        return {
            "citation_faithfulness": citation_faithfulness,
            "proof_pass_rate": proof_pass_rate,
            "static_validity_rate": static_validity_rate,
            "regression_pass_rate": regression_pass_rate,
            "overall_quality": sum(values) / len(values),
        }
```

Create `src/de_forge/api/routes/metrics.py`:

```python
"""Quality dashboard API routes."""

from fastapi import APIRouter

from de_forge.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/quality")
def quality_summary() -> dict[str, float]:
    return MetricsService().quality_snapshot(
        citation_faithfulness=1.0,
        proof_pass_rate=1.0,
        static_validity_rate=1.0,
        regression_pass_rate=1.0,
    )
```

Modify `src/de_forge/api/router.py`:

```python
from de_forge.api.routes import metrics, review, runs
```

Add:

```python
api_router.include_router(metrics.router)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_metrics.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/metrics.py src/de_forge/api/routes/metrics.py src/de_forge/api/router.py tests/unit/services/test_metrics.py tests/integration/api/test_api_routes.py
git commit -m "feat(metrics): add quality dashboard snapshot endpoint"
```

---

### Task 7: Minimal trust-oriented HTML review page

**Files:**
- Create: `src/de_forge/api/routes/ui.py`
- Modify: `src/de_forge/api/router.py`
- Modify: `tests/integration/api/test_api_routes.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/integration/api/test_api_routes.py`:

```python

def test_review_ui_page_contains_trust_columns() -> None:
    client = TestClient(app)

    response = client.get("/api/ui/review")

    assert response.status_code == 200
    assert "Evidence quote" in response.text
    assert "Detection logic" in response.text
    assert "Sigma condition" in response.text
    assert "Proof status" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/api/test_api_routes.py::test_review_ui_page_contains_trust_columns -v
```

Expected: FAIL with 404 for UI route.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/api/routes/ui.py`:

```python
"""Minimal trust-oriented HTML UI routes."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ui", tags=["ui"])


@router.get("/review", response_class=HTMLResponse)
def review_page() -> str:
    return """
    <html>
      <head><title>DE-Forge Review</title></head>
      <body>
        <h1>Rule Review</h1>
        <table>
          <thead>
            <tr>
              <th>Evidence quote</th>
              <th>Detection logic</th>
              <th>Sigma condition</th>
              <th>Proof status</th>
              <th>Validation score</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </body>
    </html>
    """
```

Modify `src/de_forge/api/router.py`:

```python
from de_forge.api.routes import metrics, review, runs, ui
```

Add:

```python
api_router.include_router(ui.router)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/api/routes/ui.py src/de_forge/api/router.py tests/integration/api/test_api_routes.py
git commit -m "feat(ui): add minimal rule review page"
```

---

### Task 8: Full orchestrator/API/UI/dashboard verification

**Files:**
- Modify only if verification finds issues.

- [ ] **Step 1: Run orchestrator and API tests**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py tests/unit/services/test_review_service.py tests/unit/services/test_metrics.py tests/integration/services/test_orchestrator_golden_path.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
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

- [ ] **Step 5: Manual UI smoke test**

Run:

```bash
uvicorn de_forge.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/api/ui/review
```

Expected:

- Page loads.
- Table headers show Evidence quote, Detection logic, Sigma condition, Proof status, Validation score.

- [ ] **Step 6: Commit verification fixes if needed**

If fixes were required:

```bash
git add <fixed-files>
git commit -m "test: verify orchestrator api and review UI"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this plan:

- State machine and no raw-report-to-rule transition: Tasks 1-2.
- Auto/cautious modes: Task 3.
- Human review gate: Task 4.
- API routes for run/review/metrics: Tasks 5-6.
- Minimal trust-oriented UI: Task 7.
- Dashboard metric foundation: Task 6.

Deferred to later UI-specific design if desired:

- Full frontend framework.
- Interactive graph visualization.
- Rich editable Sigma review UI.
- Historical trend charts backed by persisted quality snapshots.
