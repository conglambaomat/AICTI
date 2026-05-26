# DE-Forge Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden DE-Forge SOTA Core v2 into a production-grade, fail-closed, evidence-graph controlled detection engineering pipeline.

**Architecture:** Implement layered hardening in invariant order: close bypasses first, centralize export/proof/provenance gates, add relational graph/lineage models, then add PDF/LLM/agent production wiring and operations hardening. Existing happy-path behavior must keep passing, but production export must require compiler provenance, graph lineage, validation coverage, proof coverage, and latest human approval.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2, SQLite default runtime, pytest, pytest-asyncio, httpx, ruff, mypy.

---

## Scope note

This spec covers several subsystems. To keep implementation safe, this plan is a master plan split into reviewable phase tasks. Each task must be implemented and committed independently, with spec compliance review and code quality review before moving to the next task.

## File structure map

### Phase 1: bypass and invariant gates

- Modify: `src/de_forge/core/config.py` — add production-safe flags for seed route mounting and model override behavior.
- Modify: `src/de_forge/main.py` — mount seed routes only when explicitly enabled.
- Modify: `src/de_forge/api/routes/pipeline.py` — move seed endpoints into a separate router and keep production router clean.
- Create: `src/de_forge/services/export_eligibility.py` — central fail-closed export gate.
- Create: `src/de_forge/services/proof_coverage.py` — required proof coverage policy.
- Modify: `src/de_forge/services/review.py` — delegate export checks to policy services where appropriate and keep latest-review semantics.
- Modify: `src/de_forge/api/routes/pipeline.py` — export route calls `ExportEligibilityService`.
- Modify: `src/de_forge/services/orchestrator.py` — do not reuse rules without compiler provenance.
- Modify: `src/de_forge/services/state_machine.py` — remove direct DetectionSpec-to-review shortcut.
- Test: `tests/integration/api/test_seed_routes_production_gate.py`.
- Test: `tests/unit/services/test_proof_coverage.py`.
- Test: `tests/unit/services/test_export_eligibility.py`.
- Test: `tests/integration/api/test_export_production_gates.py`.
- Test: `tests/unit/services/test_state_machine_gates.py`.

### Phase 2: schema, lineage, graph, retrieval, review

- Modify: `src/de_forge/models/contract.py` — add graph, AST, compiled Sigma, retrieval link models and constraints.
- Modify: `src/de_forge/models/artifact.py` — add relationship-compatible artifact link model or keep in contract module if project pattern favors it.
- Create migration: `alembic/versions/<revision>_production_lineage_graph.py`.
- Create: `src/de_forge/services/evidence_graph.py` — graph node/edge persistence and path validation.
- Create: `src/de_forge/services/artifact_lineage.py` — artifact link persistence and lineage validation.
- Modify: `src/de_forge/services/retrieval_audit.py` — use evidence-to-retrieval links instead of chunk-only mapping.
- Modify: `src/de_forge/services/schema_guard.py` — validate critical SOTA tables/columns/indexes.
- Modify: `src/de_forge/services/review.py` — remove dynamic insert after stable schema is guaranteed.
- Test: `tests/integration/db/test_production_lineage_schema.py`.
- Test: `tests/unit/services/test_evidence_graph.py`.
- Test: `tests/unit/services/test_artifact_lineage.py`.
- Test: `tests/unit/services/test_retrieval_audit_lineage.py`.
- Test: `tests/unit/services/test_schema_guard.py`.

### Phase 3: PDF, LLM, controlled agents

- Create: `src/de_forge/services/pdf_text_extraction.py` — deterministic text-based PDF extraction boundary.
- Modify: `src/de_forge/services/ingestion.py` — accept extracted PDF text while preserving offsets.
- Modify: `src/de_forge/api/routes/pipeline.py` and `src/de_forge/api/routes/ingestion.py` — use PDF extraction service for PDFs.
- Modify: `src/de_forge/services/llm_client.py` — enforce single model in production and add concrete OpenAI-compatible transport if absent.
- Modify: `src/de_forge/agents/base.py` — enforce citation-required agent outputs.
- Modify: `src/de_forge/schemas/agent_io.py` — add role citation policy fields if needed.
- Test: `tests/unit/services/test_pdf_text_extraction.py`.
- Test: `tests/integration/api/test_pdf_ingestion.py`.
- Test: `tests/unit/services/test_llm_client_policy.py`.
- Test: `tests/unit/agents/test_agent_citation_policy.py`.

### Phase 4: operations, performance, docs

- Modify: `src/de_forge/services/metrics.py` — replace table `.all()` scans with aggregate SQL.
- Modify: `src/de_forge/main.py` — add `/ready` and seed/model/schema readiness checks.
- Modify: `src/de_forge/api/routes/review.py` or `src/de_forge/api/routes/pipeline.py` — remove/deprecate non-authoritative legacy review behavior.
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md` — update production-hardening status.
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md` — add hardening changelog entry.
- Test: `tests/unit/services/test_metrics.py`.
- Test: `tests/integration/api/test_readiness.py`.
- Test: `tests/integration/api/test_legacy_review_non_authoritative.py`.
- Verification: docs preflight, unit, integration, E2E, mypy, ruff.

---

## Phase 1A — Disable production seed routes

### Task 1: Add seed route configuration flag

**Files:**
- Modify: `src/de_forge/core/config.py`
- Test: `tests/integration/api/test_seed_routes_production_gate.py`

- [ ] **Step 1: Write the failing test**

Create `tests/integration/api/test_seed_routes_production_gate.py` with:

```python
from fastapi.testclient import TestClient

from de_forge.main import app


def test_seed_routes_are_not_mounted_by_default() -> None:
    client = TestClient(app)

    response = client.post("/v1/pipeline:seed")

    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/integration/api/test_seed_routes_production_gate.py::test_seed_routes_are_not_mounted_by_default -v
```

Expected: FAIL because `/v1/pipeline:seed` currently returns 201 or reaches route logic.

- [ ] **Step 3: Add configuration flag**

Modify `src/de_forge/core/config.py` inside `Settings`:

```python
    enable_dev_seed_routes: bool = Field(
        default=False,
        description="Mount development-only seed routes when explicitly enabled.",
    )
```

- [ ] **Step 4: Run test again**

Run the same test.

Expected: still FAIL until route mounting is changed.

- [ ] **Step 5: Commit**

Do not commit yet if Task 2 follows immediately in the same red-green unit. Commit after Task 2 passes.

### Task 2: Split seed routes from production router

**Files:**
- Modify: `src/de_forge/api/routes/pipeline.py`
- Modify: `src/de_forge/main.py`
- Test: `tests/integration/api/test_seed_routes_production_gate.py`

- [ ] **Step 1: Keep the failing test from Task 1**

The test remains:

```python
def test_seed_routes_are_not_mounted_by_default() -> None:
    client = TestClient(app)
    response = client.post("/v1/pipeline:seed")
    assert response.status_code == 404
```

- [ ] **Step 2: Move seed endpoints to a separate router**

In `src/de_forge/api/routes/pipeline.py`, add near existing routers:

```python
seed_router = APIRouter(prefix="/v1", tags=["pipeline-seed"])
```

Change decorators:

```python
@router.post("/pipeline:seed", status_code=201)
```

to:

```python
@seed_router.post("/pipeline:seed", status_code=201)
```

and change:

```python
@router.post("/pipeline:seed-abstain", status_code=201)
```

to:

```python
@seed_router.post("/pipeline:seed-abstain", status_code=201)
```

- [ ] **Step 3: Mount seed router only when explicitly enabled**

In `src/de_forge/main.py`, import `seed_router`:

```python
from de_forge.api.routes.pipeline import seed_router as pipeline_seed_router
```

Then mount only when safe:

```python
if settings.enable_dev_seed_routes and settings.env in {"development", "test"}:
    app.include_router(pipeline_seed_router)
```

- [ ] **Step 4: Run production seed route test**

Run:

```bash
pytest tests/integration/api/test_seed_routes_production_gate.py -v
```

Expected: PASS.

- [ ] **Step 5: Add opt-in seed route test**

Extend `tests/integration/api/test_seed_routes_production_gate.py` with an app factory-style test that creates a temporary FastAPI app and explicitly includes `seed_router`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from de_forge.api.routes.pipeline import seed_router


def test_seed_router_can_be_mounted_explicitly_for_dev_tools() -> None:
    dev_app = FastAPI()
    dev_app.include_router(seed_router)
    client = TestClient(dev_app)

    response = client.post("/v1/pipeline:seed")

    assert response.status_code in {201, 500}
```

The assertion allows 500 because this isolated app may not have DB dependency overrides. The purpose is to verify the router is explicitly mountable but not production-mounted.

- [ ] **Step 6: Run affected API tests**

Run:

```bash
pytest tests/integration/api/test_seed_routes_production_gate.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/core/config.py src/de_forge/api/routes/pipeline.py src/de_forge/main.py tests/integration/api/test_seed_routes_production_gate.py
git commit -m "fix(api): disable seed routes by default"
```

---

## Phase 1B — Proof coverage policy

### Task 3: Add ProofCoverageService with missing-proof failure

**Files:**
- Create: `src/de_forge/services/proof_coverage.py`
- Test: `tests/unit/services/test_proof_coverage.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_proof_coverage.py`:

```python
import pytest

from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService


def test_missing_required_proof_blocks_selection() -> None:
    service = ProofCoverageService()

    with pytest.raises(ProofCoverageError, match="missing required proof obligations"):
        service.assert_coverage_satisfied(
            run_id="run-1",
            rule_id="rule-1",
            proof_rows=[
                {"run_id": "run-1", "rule_candidate_id": "rule-1", "claim_type": "citation_faithful", "status": "proven", "justification": "exact quote verified"},
            ],
        )


def test_all_required_proofs_proven_passes() -> None:
    service = ProofCoverageService()
    rows = [
        {"run_id": "run-1", "rule_candidate_id": "rule-1", "claim_type": claim_type, "status": "proven", "justification": "verified"}
        for claim_type in service.required_claim_types()
    ]

    service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
pytest tests/unit/services/test_proof_coverage.py -v
```

Expected: FAIL with import error for `de_forge.services.proof_coverage`.

- [ ] **Step 3: Implement minimal service**

Create `src/de_forge/services/proof_coverage.py`:

```python
from __future__ import annotations

from collections.abc import Iterable, Mapping


class ProofCoverageError(ValueError):
    pass


_REQUIRED_CLAIMS = {
    "detects_report_behavior",
    "not_overbroad",
    "telemetry_fields_exist",
    "positive_tests_pass",
    "benign_baseline_not_matched",
    "citation_faithful",
    "oracle_expectations_satisfied",
    "regression_safe",
}

_NA_ALLOWED = {
    "positive_tests_pass",
    "benign_baseline_not_matched",
    "oracle_expectations_satisfied",
    "regression_safe",
}


class ProofCoverageService:
    def required_claim_types(self) -> set[str]:
        return set(_REQUIRED_CLAIMS)

    def assert_coverage_satisfied(
        self,
        *,
        run_id: str,
        rule_id: str,
        proof_rows: Iterable[Mapping[str, object]],
    ) -> None:
        current: dict[str, Mapping[str, object]] = {}
        for row in proof_rows:
            if row.get("run_id") != run_id or row.get("rule_candidate_id") != rule_id:
                continue
            claim_type = str(row.get("claim_type"))
            if claim_type in current:
                raise ProofCoverageError(f"duplicate current proof obligation: {claim_type}")
            current[claim_type] = row

        missing = sorted(_REQUIRED_CLAIMS - set(current))
        if missing:
            raise ProofCoverageError(
                "missing required proof obligations: " + ", ".join(missing)
            )

        for claim_type in sorted(_REQUIRED_CLAIMS):
            row = current[claim_type]
            status = str(row.get("status"))
            justification = str(row.get("justification") or "")
            if status == "proven":
                continue
            if status == "not_applicable" and claim_type in _NA_ALLOWED and justification:
                continue
            raise ProofCoverageError(f"proof obligation {claim_type} is {status}")
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest tests/unit/services/test_proof_coverage.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/proof_coverage.py tests/unit/services/test_proof_coverage.py
git commit -m "feat(proof): enforce required proof coverage"
```

### Task 4: Cover wrong-scope, failed, unknown, and not-applicable proof cases

**Files:**
- Modify: `tests/unit/services/test_proof_coverage.py`
- Modify: `src/de_forge/services/proof_coverage.py`

- [ ] **Step 1: Add failing edge-case tests**

Append to `tests/unit/services/test_proof_coverage.py`:

```python
def _complete_rows(status: str = "proven", justification: str = "verified") -> list[dict[str, str]]:
    service = ProofCoverageService()
    return [
        {"run_id": "run-1", "rule_candidate_id": "rule-1", "claim_type": claim_type, "status": status, "justification": justification}
        for claim_type in service.required_claim_types()
    ]


def test_wrong_scope_proofs_do_not_count() -> None:
    service = ProofCoverageService()
    rows = [
        {**row, "run_id": "other-run"}
        for row in _complete_rows()
    ]

    with pytest.raises(ProofCoverageError, match="missing required proof obligations"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_failed_or_unknown_proof_blocks_selection() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    rows[0]["status"] = "failed"

    with pytest.raises(ProofCoverageError, match="proof obligation"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_unjustified_not_applicable_blocks_selection() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    for row in rows:
        if row["claim_type"] == "oracle_expectations_satisfied":
            row["status"] = "not_applicable"
            row["justification"] = ""

    with pytest.raises(ProofCoverageError, match="oracle_expectations_satisfied"):
        service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)


def test_allowed_justified_not_applicable_passes_for_conditional_claim() -> None:
    service = ProofCoverageService()
    rows = _complete_rows()
    for row in rows:
        if row["claim_type"] == "oracle_expectations_satisfied":
            row["status"] = "not_applicable"
            row["justification"] = "no oracle case is available for this report"

    service.assert_coverage_satisfied(run_id="run-1", rule_id="rule-1", proof_rows=rows)
```

- [ ] **Step 2: Run tests**

Run:

```bash
pytest tests/unit/services/test_proof_coverage.py -v
```

Expected: PASS if Task 3 implementation already covers these cases. If any fail, adjust `ProofCoverageService` only to satisfy the explicit policy.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/services/test_proof_coverage.py src/de_forge/services/proof_coverage.py
git commit -m "test(proof): cover proof coverage edge cases"
```

### Task 5: Integrate ProofCoverageService with persisted proof checks

**Files:**
- Modify: `src/de_forge/services/validation_proof_persistence.py`
- Test: `tests/unit/services/test_validation_proof_persistence.py` or create if absent

- [ ] **Step 1: Write failing persisted proof test**

Add to `tests/unit/services/test_validation_proof_persistence.py`:

```python
import pytest

from de_forge.models import GeneratedRule, ProofObligationRecord
from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService
from de_forge.core.errors import ProofObligationError


def test_persisted_proof_verification_requires_full_coverage(db_session) -> None:
    db_session.add(GeneratedRule(id="rule-1", detection_spec_id="spec-1", rule_content="title: r"))
    db_session.add(
        ProofObligationRecord(
            id="proof-1",
            run_id="run-1",
            rule_candidate_id="rule-1",
            claim_type="citation_faithful",
            claim_text="citation exact",
            required_artifact_types="[]",
            status="proven",
            justification="verified",
        )
    )
    db_session.commit()

    service = ValidationProofPersistenceService(db_session)

    with pytest.raises(ProofObligationError, match="missing required proof obligations"):
        service.verify_persisted_proofs_selectable(run_id="run-1", rule_id="rule-1")
```

If the project uses a different fixture name than `db_session`, adapt to the existing service-test fixture before implementation.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_validation_proof_persistence.py::test_persisted_proof_verification_requires_full_coverage -v
```

Expected: FAIL because current persisted verification accepts any existing proven subset.

- [ ] **Step 3: Integrate proof coverage policy**

In `src/de_forge/services/validation_proof_persistence.py`, import:

```python
from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService
```

Inside `verify_persisted_proofs_selectable`, replace row-by-row status-only checking with:

```python
        try:
            ProofCoverageService().assert_coverage_satisfied(
                run_id=run_id,
                rule_id=rule_id,
                proof_rows=[
                    {
                        "run_id": obligation.run_id,
                        "rule_candidate_id": obligation.rule_candidate_id,
                        "claim_type": obligation.claim_type,
                        "status": obligation.status,
                        "justification": obligation.justification,
                    }
                    for obligation in obligations
                ],
            )
        except ProofCoverageError as exc:
            raise ProofObligationError(str(exc)) from exc
        return True
```

- [ ] **Step 4: Run targeted test**

Run:

```bash
pytest tests/unit/services/test_validation_proof_persistence.py::test_persisted_proof_verification_requires_full_coverage -v
```

Expected: PASS.

- [ ] **Step 5: Run proof-related tests**

Run:

```bash
pytest tests/unit/services/test_proof_coverage.py tests/unit/services/test_validation_proof_persistence.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/validation_proof_persistence.py tests/unit/services/test_validation_proof_persistence.py
git commit -m "fix(proof): require full persisted proof coverage"
```

---

## Phase 1C — Export eligibility and compiler provenance

### Task 6: Add generated rule provenance fields

**Files:**
- Modify: `src/de_forge/models/contract.py`
- Create migration: `alembic/versions/<revision>_add_rule_provenance.py`
- Test: `tests/integration/db/test_generated_rule_provenance_schema.py`

- [ ] **Step 1: Write failing schema test**

Create `tests/integration/db/test_generated_rule_provenance_schema.py`:

```python
from sqlalchemy import inspect

from de_forge.db.session import engine


def test_generated_rules_has_compiler_provenance_columns() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("generated_rules")}

    assert "generation_source" in columns
    assert "detection_ast_id" in columns
    assert "compiled_sigma_id" in columns
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/db/test_generated_rule_provenance_schema.py -v
```

Expected: FAIL because columns do not exist.

- [ ] **Step 3: Modify model**

In `GeneratedRule` in `src/de_forge/models/contract.py`, add:

```python
    generation_source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual_draft")
    detection_ast_id: Mapped[str | None] = mapped_column(String(36))
    compiled_sigma_id: Mapped[str | None] = mapped_column(String(36))
```

- [ ] **Step 4: Add migration**

Create Alembic migration with:

```python
def upgrade() -> None:
    op.add_column("generated_rules", sa.Column("generation_source", sa.String(length=30), nullable=False, server_default="manual_draft"))
    op.add_column("generated_rules", sa.Column("detection_ast_id", sa.String(length=36), nullable=True))
    op.add_column("generated_rules", sa.Column("compiled_sigma_id", sa.String(length=36), nullable=True))


def downgrade() -> None:
    op.drop_column("generated_rules", "compiled_sigma_id")
    op.drop_column("generated_rules", "detection_ast_id")
    op.drop_column("generated_rules", "generation_source")
```

Use the repository's existing Alembic revision pattern.

- [ ] **Step 5: Run migration/schema test**

Run:

```bash
pytest tests/integration/db/test_generated_rule_provenance_schema.py tests/integration/db -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/models/contract.py alembic/versions tests/integration/db/test_generated_rule_provenance_schema.py
git commit -m "feat(db): add generated rule provenance fields"
```

### Task 7: Add CompilerProvenanceService

**Files:**
- Create: `src/de_forge/services/compiler_provenance.py`
- Test: `tests/unit/services/test_compiler_provenance.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_compiler_provenance.py`:

```python
import pytest

from de_forge.services.compiler_provenance import CompilerProvenanceError, CompilerProvenanceService


class Rule:
    def __init__(self, generation_source: str, detection_ast_id: str | None, compiled_sigma_id: str | None) -> None:
        self.generation_source = generation_source
        self.detection_ast_id = detection_ast_id
        self.compiled_sigma_id = compiled_sigma_id


def test_manual_rule_fails_production_provenance() -> None:
    service = CompilerProvenanceService()
    rule = Rule("manual_draft", None, None)

    with pytest.raises(CompilerProvenanceError, match="compiler-generated"):
        service.assert_rule_has_compiler_provenance(rule)


def test_compiler_rule_with_ast_and_compiled_sigma_passes() -> None:
    service = CompilerProvenanceService()
    rule = Rule("compiler", "ast-1", "sigma-1")

    service.assert_rule_has_compiler_provenance(rule)
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_compiler_provenance.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement service**

Create `src/de_forge/services/compiler_provenance.py`:

```python
from __future__ import annotations

from typing import Protocol


class CompilerProvenanceError(ValueError):
    pass


class RuleWithProvenance(Protocol):
    generation_source: str
    detection_ast_id: str | None
    compiled_sigma_id: str | None


class CompilerProvenanceService:
    def assert_rule_has_compiler_provenance(self, rule: RuleWithProvenance) -> None:
        if rule.generation_source != "compiler":
            raise CompilerProvenanceError("rule is not compiler-generated")
        if not rule.detection_ast_id:
            raise CompilerProvenanceError("rule is missing Detection AST provenance")
        if not rule.compiled_sigma_id:
            raise CompilerProvenanceError("rule is missing compiled Sigma provenance")
```

- [ ] **Step 4: Run test**

Run:

```bash
pytest tests/unit/services/test_compiler_provenance.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/compiler_provenance.py tests/unit/services/test_compiler_provenance.py
git commit -m "feat(rule): add compiler provenance gate"
```

### Task 8: Add ExportEligibilityService skeleton with compiler/proof checks

**Files:**
- Create: `src/de_forge/services/export_eligibility.py`
- Test: `tests/unit/services/test_export_eligibility.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_export_eligibility.py`:

```python
import pytest

from de_forge.services.export_eligibility import ExportBlockedReason, ExportEligibilityService


class FakeRule:
    id = "rule-1"
    detection_spec_id = "spec-1"
    rule_content = "title: rule"
    generation_source = "manual_draft"
    detection_ast_id = None
    compiled_sigma_id = None


class FakeRepo:
    def get_run(self, run_id: str):
        return type("Run", (), {"run_id": run_id, "rule_id": "rule-1", "detection_spec_id": "spec-1", "stage": "awaiting_review"})()

    def get_rule(self, rule_id: str):
        return FakeRule()

    def get_detection_spec(self, spec_id: str):
        return type("Spec", (), {"id": spec_id, "is_validated": True})()

    def get_proof_rows(self, run_id: str, rule_id: str):
        return []

    def latest_review_decision(self, run_id: str, rule_id: str):
        return "approved"


def test_export_blocks_rule_without_compiler_provenance() -> None:
    service = ExportEligibilityService(repository=FakeRepo())

    with pytest.raises(ExportBlockedReason, match="COMPILER_PROVENANCE_MISSING"):
        service.assert_exportable(run_id="run-1", rule_id="rule-1")
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_export_eligibility.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement minimal service**

Create `src/de_forge/services/export_eligibility.py`:

```python
from __future__ import annotations

from typing import Protocol

from de_forge.services.compiler_provenance import CompilerProvenanceError, CompilerProvenanceService
from de_forge.services.proof_coverage import ProofCoverageError, ProofCoverageService


class ExportBlockedReason(ValueError):
    pass


class ExportEligibilityRepository(Protocol):
    def get_run(self, run_id: str): ...
    def get_rule(self, rule_id: str): ...
    def get_detection_spec(self, spec_id: str): ...
    def get_proof_rows(self, run_id: str, rule_id: str): ...
    def latest_review_decision(self, run_id: str, rule_id: str): ...


class ExportEligibilityService:
    def __init__(self, repository: ExportEligibilityRepository) -> None:
        self.repository = repository
        self.compiler_provenance = CompilerProvenanceService()
        self.proof_coverage = ProofCoverageService()

    def assert_exportable(self, *, run_id: str, rule_id: str) -> None:
        run = self.repository.get_run(run_id)
        if run is None:
            raise ExportBlockedReason("PIPELINE_RUN_MISSING")
        if run.rule_id != rule_id:
            raise ExportBlockedReason("RULE_MAPPING_MISMATCH")

        rule = self.repository.get_rule(rule_id)
        if rule is None or not rule.rule_content:
            raise ExportBlockedReason("GENERATED_RULE_MISSING")

        spec = self.repository.get_detection_spec(rule.detection_spec_id)
        if spec is None or not spec.is_validated:
            raise ExportBlockedReason("DETECTION_SPEC_MISSING")

        try:
            self.compiler_provenance.assert_rule_has_compiler_provenance(rule)
        except CompilerProvenanceError as exc:
            raise ExportBlockedReason("COMPILER_PROVENANCE_MISSING") from exc

        try:
            self.proof_coverage.assert_coverage_satisfied(
                run_id=run_id,
                rule_id=rule_id,
                proof_rows=self.repository.get_proof_rows(run_id, rule_id),
            )
        except ProofCoverageError as exc:
            raise ExportBlockedReason("PROOF_COVERAGE_MISSING") from exc

        if self.repository.latest_review_decision(run_id, rule_id) != "approved":
            raise ExportBlockedReason("HUMAN_APPROVAL_REQUIRED")
```

- [ ] **Step 4: Run test**

Run:

```bash
pytest tests/unit/services/test_export_eligibility.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/export_eligibility.py tests/unit/services/test_export_eligibility.py
git commit -m "feat(export): add centralized eligibility gate"
```

### Task 9: Wire export route to ExportEligibilityService

**Files:**
- Modify: `src/de_forge/services/export_eligibility.py`
- Modify: `src/de_forge/api/routes/pipeline.py`
- Test: `tests/integration/api/test_export_production_gates.py`

- [ ] **Step 1: Write failing integration test**

Create `tests/integration/api/test_export_production_gates.py` with a DB-backed app fixture following existing integration patterns. Add:

```python
def test_export_blocks_manual_rule_without_compiler_provenance(client, db_session) -> None:
    # Arrange using existing model classes and helper patterns from API tests.
    # Persist Report, DetectionSpec(validated), GeneratedRule(generation_source='manual_draft'), PipelineRunRecord,
    # complete proof rows, and approved review decision.
    # Act
    response = client.post("/v1/exports/sigma", json={"run_id": "run-1"})

    assert response.status_code == 403
    assert response.json()["detail"] == "COMPILER_PROVENANCE_MISSING"
```

Use the exact fixture names from `tests/integration/api/test_api_routes.py`. If those fixtures are not reusable, create a local `TestClient` with dependency override like existing E2E tests.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py::test_export_blocks_manual_rule_without_compiler_provenance -v
```

Expected: FAIL because export route still uses `ReviewService.assert_can_export` only.

- [ ] **Step 3: Add SQLAlchemy-backed repository adapter**

In `src/de_forge/services/export_eligibility.py`, add:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec, GeneratedRule, PipelineRunRecord, ProofObligationRecord
from de_forge.services.review import ReviewService


class SqlAlchemyExportEligibilityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_run(self, run_id: str):
        return self.db.execute(
            select(PipelineRunRecord).where(PipelineRunRecord.run_id == run_id)
        ).scalar_one_or_none()

    def get_rule(self, rule_id: str):
        return self.db.get(GeneratedRule, rule_id)

    def get_detection_spec(self, spec_id: str):
        return self.db.get(DetectionSpec, spec_id)

    def get_proof_rows(self, run_id: str, rule_id: str):
        return [
            {
                "run_id": row.run_id,
                "rule_candidate_id": row.rule_candidate_id,
                "claim_type": row.claim_type,
                "status": row.status,
                "justification": row.justification,
            }
            for row in self.db.execute(
                select(ProofObligationRecord).where(
                    ProofObligationRecord.run_id == run_id,
                    ProofObligationRecord.rule_candidate_id == rule_id,
                )
            ).scalars().all()
        ]

    def latest_review_decision(self, run_id: str, rule_id: str):
        decision = ReviewService(self.db)._get_latest_decision(rule_id, run_id=run_id)
        return decision.decision if decision is not None else None
```

- [ ] **Step 4: Wire export route**

In `src/de_forge/api/routes/pipeline.py`, import:

```python
from de_forge.services.export_eligibility import ExportBlockedReason, ExportEligibilityService, SqlAlchemyExportEligibilityRepository
```

Replace `ReviewService.assert_can_export(...)` in `export_sigma` with:

```python
    try:
        ExportEligibilityService(SqlAlchemyExportEligibilityRepository(db)).assert_exportable(
            run_id=payload.run_id,
            rule_id=rule_id,
        )
    except ExportBlockedReason as exc:
        return JSONResponse(status_code=403, content={"detail": str(exc)})
```

- [ ] **Step 5: Run targeted test**

Run:

```bash
pytest tests/integration/api/test_export_production_gates.py -v
```

Expected: PASS.

- [ ] **Step 6: Run existing export/review tests**

Run:

```bash
pytest tests/unit/services/test_review_service.py tests/integration/api/test_api_routes.py tests/integration/e2e/test_sota_pipeline_e2e.py -v
```

Expected: PASS after fixtures are updated to create complete proof coverage and compiler provenance where production export is expected.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/services/export_eligibility.py src/de_forge/api/routes/pipeline.py tests/integration/api/test_export_production_gates.py tests/integration/e2e/test_sota_pipeline_e2e.py
git commit -m "fix(export): enforce production eligibility gates"
```

---

## Phase 1D — State machine hardening

### Task 10: Remove DetectionSpec-to-review shortcut

**Files:**
- Modify: `src/de_forge/services/state_machine.py`
- Test: `tests/unit/services/test_state_machine_gates.py`

- [ ] **Step 1: Add failing state transition test**

In `tests/unit/services/test_state_machine_gates.py`, add:

```python
def test_detection_spec_ready_cannot_transition_directly_to_awaiting_review() -> None:
    machine = PipelineStateMachine()

    assert not machine.can_transition(RunState.DETECTION_SPEC_READY, RunState.AWAITING_REVIEW)
```

Use the existing class/enum names from the file. If they differ, adapt names to current code before implementation.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py::test_detection_spec_ready_cannot_transition_directly_to_awaiting_review -v
```

Expected: FAIL because the shortcut is currently allowed.

- [ ] **Step 3: Remove shortcut**

In `src/de_forge/services/state_machine.py`, remove the allowed transition:

```python
RunState.DETECTION_SPEC_READY: {RunState.AWAITING_REVIEW, ...}
```

so `AWAITING_REVIEW` is not reachable directly from `DETECTION_SPEC_READY`.

If intermediate states do not exist yet, do not add speculative states in this task; rely on existing service gates and add explicit states in a later task only if current tests require it.

- [ ] **Step 4: Run state machine tests**

Run:

```bash
pytest tests/unit/services/test_state_machine_gates.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/state_machine.py tests/unit/services/test_state_machine_gates.py
git commit -m "fix(orchestrator): reject detection spec review shortcut"
```

---

## Phase 2A — Evidence graph core

### Task 11: Add graph node and edge models

**Files:**
- Modify: `src/de_forge/models/contract.py`
- Create migration: `alembic/versions/<revision>_add_evidence_graph.py`
- Test: `tests/integration/db/test_evidence_graph_schema.py`

- [ ] **Step 1: Write failing schema test**

Create `tests/integration/db/test_evidence_graph_schema.py`:

```python
from sqlalchemy import inspect

from de_forge.db.session import engine


def test_graph_tables_exist_with_required_columns() -> None:
    inspector = inspect(engine)
    assert "graph_nodes" in inspector.get_table_names()
    assert "graph_edges" in inspector.get_table_names()

    node_columns = {column["name"] for column in inspector.get_columns("graph_nodes")}
    edge_columns = {column["name"] for column in inspector.get_columns("graph_edges")}

    assert {"id", "run_id", "node_type", "ref_table", "ref_id", "payload_json", "created_at"} <= node_columns
    assert {"id", "run_id", "source_node_id", "target_node_id", "edge_type", "payload_json", "created_at"} <= edge_columns
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/db/test_evidence_graph_schema.py -v
```

Expected: FAIL because tables do not exist.

- [ ] **Step 3: Add models**

In `src/de_forge/models/contract.py`, add `GraphNode` and `GraphEdge` classes with the columns and constraints defined in the design spec.

- [ ] **Step 4: Add migration**

Create migration that creates `graph_nodes` and `graph_edges` with indexes and constraints.

- [ ] **Step 5: Run schema tests**

Run:

```bash
pytest tests/integration/db/test_evidence_graph_schema.py tests/integration/db -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/models/contract.py alembic/versions tests/integration/db/test_evidence_graph_schema.py
git commit -m "feat(db): add evidence graph tables"
```

### Task 12: Add EvidenceGraphService path validation

**Files:**
- Create: `src/de_forge/services/evidence_graph.py`
- Test: `tests/unit/services/test_evidence_graph.py`

- [ ] **Step 1: Write failing service tests**

Create `tests/unit/services/test_evidence_graph.py`:

```python
import pytest

from de_forge.services.evidence_graph import EvidenceGraphError, EvidenceGraphService


def test_missing_required_graph_path_blocks_export() -> None:
    service = EvidenceGraphService(db=None)

    with pytest.raises(EvidenceGraphError, match="evidence graph path incomplete"):
        service.assert_export_path_complete(run_id="run-1", rule_id="rule-1")
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_evidence_graph.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement service skeleton**

Create `src/de_forge/services/evidence_graph.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import Session


class EvidenceGraphError(ValueError):
    pass


class EvidenceGraphService:
    def __init__(self, db: Session | None) -> None:
        self.db = db

    def assert_export_path_complete(self, *, run_id: str, rule_id: str) -> None:
        if self.db is None:
            raise EvidenceGraphError("evidence graph path incomplete")
        # Real DB traversal is added in the next task after graph persistence is wired.
        raise EvidenceGraphError("evidence graph path incomplete")
```

- [ ] **Step 4: Run test**

Run:

```bash
pytest tests/unit/services/test_evidence_graph.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/evidence_graph.py tests/unit/services/test_evidence_graph.py
git commit -m "feat(graph): add export path validation service"
```

### Task 13: Persist graph nodes and edges for pipeline artifacts

**Files:**
- Modify: `src/de_forge/services/evidence_graph.py`
- Modify: `src/de_forge/services/orchestrator.py`
- Modify: `src/de_forge/services/review.py`
- Test: `tests/integration/e2e/test_sota_pipeline_e2e.py`

- [ ] **Step 1: Add failing E2E assertion**

In successful pipeline E2E test, after approval and before export, assert graph path exists:

```python
from de_forge.services.evidence_graph import EvidenceGraphService


def test_successful_sota_pipeline_ingest_run_review_export(...):
    ...
    EvidenceGraphService(db).assert_export_path_complete(run_id=run_id, rule_id=rule_id)
```

- [ ] **Step 2: Run E2E test**

Run:

```bash
pytest tests/integration/e2e/test_sota_pipeline_e2e.py::test_successful_sota_pipeline_ingest_run_review_export -v
```

Expected: FAIL because graph path is not persisted.

- [ ] **Step 3: Implement graph persistence helpers**

In `EvidenceGraphService`, add methods:

```python
    def upsert_node(self, *, run_id: str, node_type: str, ref_table: str, ref_id: str, payload: dict[str, object] | None = None) -> str:
        ...

    def add_edge(self, *, run_id: str, source_node_id: str, target_node_id: str, edge_type: str, payload: dict[str, object] | None = None) -> str:
        ...
```

Use SQLAlchemy models `GraphNode` and `GraphEdge`, UUID ids, JSON serialization with `sort_keys=True`, and idempotent lookup by `(run_id, node_type, ref_table, ref_id)`.

- [ ] **Step 4: Wire pipeline/review graph writes**

In orchestrator, persist nodes/edges for:

```text
report -> evidence_quote -> detection_spec -> generated_rule -> validation_result -> proof_obligation
```

In review service, persist:

```text
generated_rule -> review_decision
```

- [ ] **Step 5: Implement path validation query**

`assert_export_path_complete` should query graph nodes/edges and require at least:

```text
generated_rule node exists for rule_id
review_decision node exists for run/rule
proof_obligation node exists for run/rule
detection_spec node exists upstream
```

Keep traversal simple and exact for current schema; do not implement a generic graph engine.

- [ ] **Step 6: Run E2E**

Run:

```bash
pytest tests/integration/e2e/test_sota_pipeline_e2e.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/de_forge/services/evidence_graph.py src/de_forge/services/orchestrator.py src/de_forge/services/review.py tests/integration/e2e/test_sota_pipeline_e2e.py
git commit -m "feat(graph): persist pipeline evidence graph path"
```

---

## Phase 2B — Artifact lineage links

### Task 14: Add artifact link model and migration

**Files:**
- Modify: `src/de_forge/models/artifact.py`
- Create migration: `alembic/versions/<revision>_add_artifact_links.py`
- Test: `tests/integration/db/test_artifact_links_schema.py`

- [ ] **Step 1: Write failing schema test**

Create `tests/integration/db/test_artifact_links_schema.py`:

```python
from sqlalchemy import inspect

from de_forge.db.session import engine


def test_artifact_links_table_exists() -> None:
    inspector = inspect(engine)
    assert "artifact_links" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("artifact_links")}
    assert {"id", "parent_artifact_id", "child_artifact_id", "link_type", "created_at"} <= columns
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/db/test_artifact_links_schema.py -v
```

Expected: FAIL because table does not exist.

- [ ] **Step 3: Add model and migration**

Add `ArtifactLink` model with FK parent/child to `artifacts.id`, check parent != child, and unique parent-child-link type. Add migration.

- [ ] **Step 4: Run schema tests**

Run:

```bash
pytest tests/integration/db/test_artifact_links_schema.py tests/integration/db -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/models/artifact.py alembic/versions tests/integration/db/test_artifact_links_schema.py
git commit -m "feat(db): add artifact lineage links"
```

### Task 15: Add ArtifactLineageService

**Files:**
- Create: `src/de_forge/services/artifact_lineage.py`
- Modify: `src/de_forge/services/export_eligibility.py`
- Test: `tests/unit/services/test_artifact_lineage.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_artifact_lineage.py`:

```python
import pytest

from de_forge.services.artifact_lineage import ArtifactLineageError, ArtifactLineageService


def test_missing_rule_lineage_blocks_export() -> None:
    service = ArtifactLineageService(db=None)

    with pytest.raises(ArtifactLineageError, match="artifact lineage incomplete"):
        service.assert_rule_lineage_complete(run_id="run-1", rule_id="rule-1")
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_artifact_lineage.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement service skeleton**

Create `src/de_forge/services/artifact_lineage.py`:

```python
from __future__ import annotations

from sqlalchemy.orm import Session


class ArtifactLineageError(ValueError):
    pass


class ArtifactLineageService:
    def __init__(self, db: Session | None) -> None:
        self.db = db

    def assert_rule_lineage_complete(self, *, run_id: str, rule_id: str) -> None:
        if self.db is None:
            raise ArtifactLineageError("artifact lineage incomplete")
        raise ArtifactLineageError("artifact lineage incomplete")
```

- [ ] **Step 4: Run test**

Run:

```bash
pytest tests/unit/services/test_artifact_lineage.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/artifact_lineage.py tests/unit/services/test_artifact_lineage.py
git commit -m "feat(lineage): add artifact lineage gate"
```

---

## Phase 2C — Retrieval, review constraints, schema guard

### Task 16: Add evidence retrieval link model

**Files:**
- Modify: `src/de_forge/models/contract.py`
- Create migration: `alembic/versions/<revision>_add_evidence_retrieval_links.py`
- Test: `tests/integration/db/test_evidence_retrieval_links_schema.py`

- [ ] **Step 1: Write failing schema test**

Create `tests/integration/db/test_evidence_retrieval_links_schema.py`:

```python
from sqlalchemy import inspect

from de_forge.db.session import engine


def test_evidence_retrieval_links_table_exists() -> None:
    inspector = inspect(engine)
    assert "evidence_retrieval_links" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("evidence_retrieval_links")}
    assert {"id", "run_id", "evidence_id", "retrieval_candidate_id", "created_at"} <= columns
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/db/test_evidence_retrieval_links_schema.py -v
```

Expected: FAIL.

- [ ] **Step 3: Add model and migration**

Add `EvidenceRetrievalLink` model and migration with FK to `evidence_spans.id` and `retrieval_candidates.id`.

- [ ] **Step 4: Run DB tests**

Run:

```bash
pytest tests/integration/db/test_evidence_retrieval_links_schema.py tests/integration/db -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/models/contract.py alembic/versions tests/integration/db/test_evidence_retrieval_links_schema.py
git commit -m "feat(db): link evidence to retrieval candidates"
```

### Task 17: Fail closed on ambiguous retrieval lineage

**Files:**
- Modify: `src/de_forge/services/retrieval_audit.py`
- Test: `tests/unit/services/test_retrieval_audit_lineage.py`

- [ ] **Step 1: Add failing test**

In `tests/unit/services/test_retrieval_audit_lineage.py`, add a test that creates two `RetrievalCandidate` rows for the same `run_id` and `chunk_id` from different retrieval runs, one evidence span for that chunk, and no `EvidenceRetrievalLink`.

Expected assertion:

```python
with pytest.raises(ValueError, match="ambiguous retrieval audit lineage"):
    RetrievalAuditService(db_session).get_run_evidence_lineage("run-1")
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_retrieval_audit_lineage.py::test_duplicate_chunk_candidates_require_explicit_evidence_link -v
```

Expected: FAIL because current service silently maps by chunk_id.

- [ ] **Step 3: Implement fail-closed ambiguity detection**

In `get_run_evidence_lineage`, before building `candidate_by_chunk_id`, group candidates by chunk id:

```python
candidates_by_chunk_id: dict[str, list[RetrievalCandidate]] = {}
for candidate in candidates:
    candidates_by_chunk_id.setdefault(candidate.chunk_id, []).append(candidate)

ambiguous = [chunk_id for chunk_id, rows in candidates_by_chunk_id.items() if len(rows) > 1]
if ambiguous:
    raise ValueError("ambiguous retrieval audit lineage for evidence chunks")
```

Later tasks may use `EvidenceRetrievalLink` for exact mapping; this task prevents silent wrong lineage immediately.

- [ ] **Step 4: Run retrieval tests**

Run:

```bash
pytest tests/unit/services/test_retrieval_audit_lineage.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/retrieval_audit.py tests/unit/services/test_retrieval_audit_lineage.py
git commit -m "fix(retrieval): fail closed on ambiguous evidence lineage"
```

### Task 18: Expand SchemaGuard to critical tables

**Files:**
- Modify: `src/de_forge/services/schema_guard.py`
- Test: `tests/unit/services/test_schema_guard.py`

- [ ] **Step 1: Add failing test**

In `tests/unit/services/test_schema_guard.py`, create a SQLite in-memory schema missing `graph_nodes` and assert:

```python
with pytest.raises(SchemaContractError, match="missing table graph_nodes"):
    SchemaGuard(engine).assert_contract_current()
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_schema_guard.py -v
```

Expected: FAIL because SchemaGuard only checks `agent_runs`.

- [ ] **Step 3: Add critical table registry**

In `src/de_forge/services/schema_guard.py`, define:

```python
_REQUIRED_TABLES = {
    "reports",
    "report_chunks",
    "evidence_spans",
    "graph_nodes",
    "graph_edges",
    "detection_specs",
    "generated_rules",
    "proof_obligations",
    "validation_results",
    "review_decisions",
    "pipeline_runs",
    "agent_runs",
    "retrieval_audit_runs",
    "retrieval_candidates",
}
```

In `assert_contract_current`, check missing tables before column/index checks:

```python
missing_tables = sorted(_REQUIRED_TABLES - table_names)
if missing_tables:
    raise SchemaContractError("schema drift: missing table " + missing_tables[0])
```

- [ ] **Step 4: Run schema guard tests**

Run:

```bash
pytest tests/unit/services/test_schema_guard.py -v
```

Expected: PASS.

- [ ] **Step 5: Run health/API tests**

Run:

```bash
pytest tests/integration/api/test_api_routes.py tests/integration/e2e/test_sota_runtime_truth_e2e.py -v
```

Expected: PASS after test DB setup includes new tables.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/schema_guard.py tests/unit/services/test_schema_guard.py tests/integration/e2e/test_sota_runtime_truth_e2e.py
git commit -m "fix(schema): guard critical production tables"
```

---

## Phase 3A — Text-based PDF ingestion

### Task 19: Add PDF text extraction boundary

**Files:**
- Create: `src/de_forge/services/pdf_text_extraction.py`
- Test: `tests/unit/services/test_pdf_text_extraction.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/services/test_pdf_text_extraction.py`:

```python
import pytest

from de_forge.services.pdf_text_extraction import PdfExtractionError, PdfTextExtractionService


def test_empty_pdf_bytes_fail_closed() -> None:
    service = PdfTextExtractionService()

    with pytest.raises(PdfExtractionError, match="PDF text extraction failed"):
        service.extract_text(b"")
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_pdf_text_extraction.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement fail-closed service shell**

Create `src/de_forge/services/pdf_text_extraction.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


class PdfExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class PdfPageText:
    page_number: int
    text: str
    global_char_start: int
    global_char_end: int


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    pages: list[PdfPageText]
    metadata: dict[str, object]


class PdfTextExtractionService:
    def extract_text(self, content: bytes) -> PdfExtractionResult:
        if not content:
            raise PdfExtractionError("PDF text extraction failed")
        raise PdfExtractionError("PDF text extraction failed")
```

- [ ] **Step 4: Run test**

Run:

```bash
pytest tests/unit/services/test_pdf_text_extraction.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/pdf_text_extraction.py tests/unit/services/test_pdf_text_extraction.py
git commit -m "feat(pdf): add fail-closed extraction boundary"
```

### Task 20: Implement text-based PDF extraction with approved dependency

**Files:**
- Modify: `pyproject.toml` if no existing PDF parser dependency exists
- Modify: `src/de_forge/services/pdf_text_extraction.py`
- Test: `tests/unit/services/test_pdf_text_extraction.py`

- [ ] **Step 1: Check dependency policy**

If the repo already has a PDF parser dependency, use it. If not, add a minimal maintained text extraction dependency such as `pypdf` to project metadata because PDF support is explicitly approved by the production-hardening spec.

- [ ] **Step 2: Add passing valid-PDF test**

Add a fixture PDF under `tests/fixtures/text_report.pdf` or generate one in test using the chosen dependency if supported. Test:

```python
def test_text_based_pdf_extracts_text_with_page_offsets() -> None:
    content = Path("tests/fixtures/text_report.pdf").read_bytes()

    result = PdfTextExtractionService().extract_text(content)

    assert "PowerShell" in result.text
    assert result.pages[0].page_number == 1
    assert result.pages[0].global_char_start == 0
    assert result.pages[0].global_char_end > 0
```

- [ ] **Step 3: Run test**

Run:

```bash
pytest tests/unit/services/test_pdf_text_extraction.py::test_text_based_pdf_extracts_text_with_page_offsets -v
```

Expected: FAIL until extraction is implemented.

- [ ] **Step 4: Implement extraction**

Implement with bounded parsing, page iteration, normalized text join, and fail-closed exceptions:

```python
    def extract_text(self, content: bytes) -> PdfExtractionResult:
        if not content:
            raise PdfExtractionError("PDF text extraction failed")
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise PdfExtractionError("PDF text extraction failed: encrypted PDF")
            pages = []
            parts = []
            cursor = 0
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue
                start = cursor
                parts.append(page_text)
                cursor += len(page_text)
                pages.append(PdfPageText(index, page_text, start, cursor))
                parts.append("\n")
                cursor += 1
            text = "".join(parts).strip()
            if not text:
                raise PdfExtractionError("PDF text extraction failed: no extractable text")
            return PdfExtractionResult(text=text, pages=pages, metadata={"page_count": len(reader.pages), "extractor": "pypdf"})
        except PdfExtractionError:
            raise
        except Exception as exc:
            raise PdfExtractionError("PDF text extraction failed") from exc
```

Adjust imports to match chosen library.

- [ ] **Step 5: Run PDF tests**

Run:

```bash
pytest tests/unit/services/test_pdf_text_extraction.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/de_forge/services/pdf_text_extraction.py tests/unit/services/test_pdf_text_extraction.py tests/fixtures/text_report.pdf
git commit -m "feat(pdf): extract text-based reports with offsets"
```

### Task 21: Wire PDF ingestion routes

**Files:**
- Modify: `src/de_forge/api/routes/pipeline.py`
- Modify: `src/de_forge/api/routes/ingestion.py`
- Modify: `src/de_forge/services/ingestion.py`
- Test: `tests/integration/api/test_pdf_ingestion.py`

- [ ] **Step 1: Write failing API test**

Create `tests/integration/api/test_pdf_ingestion.py`:

```python
def test_pdf_upload_ingests_text_report(client) -> None:
    content = Path("tests/fixtures/text_report.pdf").read_bytes()

    response = client.post(
        "/v1/ingest",
        files={"file": ("text_report.pdf", content, "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "ingested"
```

Use the actual current PDF upload endpoint path from existing ingestion tests.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/api/test_pdf_ingestion.py -v
```

Expected: FAIL with 415 PDF unsupported.

- [ ] **Step 3: Wire PDF extraction**

In ingestion routes, replace PDF rejection with:

```python
if filename.lower().endswith(".pdf"):
    extraction = PdfTextExtractionService().extract_text(content_bytes)
    result = IngestionService(db).ingest(
        source_type="pdf",
        filename=filename,
        content_bytes=extraction.text.encode("utf-8"),
        metadata={"pdf_extraction": extraction.metadata},
    )
```

If `IngestionService.ingest` does not accept metadata, add an optional `metadata` parameter and merge it into `metadata_json`.

- [ ] **Step 4: Run API PDF tests**

Run:

```bash
pytest tests/integration/api/test_pdf_ingestion.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/api/routes/pipeline.py src/de_forge/api/routes/ingestion.py src/de_forge/services/ingestion.py tests/integration/api/test_pdf_ingestion.py
git commit -m "feat(api): ingest text-based PDF reports"
```

---

## Phase 3B — LLM provider/model production policy

### Task 22: Reject model override in production

**Files:**
- Modify: `src/de_forge/services/llm_client.py`
- Test: `tests/unit/services/test_llm_client_policy.py`

- [ ] **Step 1: Write failing test**

Create or modify `tests/unit/services/test_llm_client_policy.py`:

```python
import pytest

from de_forge.services.llm_client import LLMClient, LLMRequest, ConfigurationError


class DummyTransport:
    def send(self, payload, timeout_seconds):
        raise AssertionError("transport should not be called")


def test_model_override_is_rejected() -> None:
    client = LLMClient(transport=DummyTransport(), model="cx/gpt-5.5", api_key="key")

    with pytest.raises(ConfigurationError, match="model override"):
        client.call(LLMRequest(prompt="{}", model="other-model"))
```

Use the current error class if `ConfigurationError` already exists; otherwise add it in implementation.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_llm_client_policy.py::test_model_override_is_rejected -v
```

Expected: FAIL because override is currently allowed.

- [ ] **Step 3: Implement model policy**

In `LLMClient.call`, before transport send:

```python
        if request.model and request.model != self._model:
            raise ConfigurationError("model override is not allowed")
```

Use `self._model` in payload:

```python
"model": self._model,
```

- [ ] **Step 4: Run LLM tests**

Run:

```bash
pytest tests/unit/services/test_llm_client_policy.py tests/unit/services/test_llm_client.py -v
```

Expected: PASS after updating existing tests to expect configured model.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/llm_client.py tests/unit/services/test_llm_client_policy.py tests/unit/services/test_llm_client.py
git commit -m "fix(llm): enforce single configured model"
```

### Task 23: Add concrete OpenAI-compatible transport

**Files:**
- Modify: `src/de_forge/services/llm_client.py` or create `src/de_forge/services/openai_transport.py`
- Test: `tests/unit/services/test_openai_transport.py`

- [ ] **Step 1: Write failing transport test**

Create `tests/unit/services/test_openai_transport.py`:

```python
def test_openai_transport_builds_authorized_json_request() -> None:
    sent = {}

    class FakeHttpClient:
        def post(self, url, headers, json, timeout):
            sent["url"] = url
            sent["headers"] = headers
            sent["json"] = json
            sent["timeout"] = timeout
            return FakeResponse()

    transport = OpenAICompatibleTransport(base_url="https://shopapikey.com/v1", api_key="key", http_client=FakeHttpClient())
    transport.send({"prompt": "Return JSON", "model": "cx/gpt-5.5", "temperature": 0, "max_tokens": 10, "response_format": {"type": "json_object"}, "metadata": {}}, timeout_seconds=30)

    assert sent["url"].endswith("/chat/completions")
    assert sent["headers"]["Authorization"] == "Bearer key"
    assert sent["json"]["model"] == "cx/gpt-5.5"
```

Define `FakeResponse` in the test with `.json()` and `.raise_for_status()` matching the implementation contract.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/services/test_openai_transport.py -v
```

Expected: FAIL with missing `OpenAICompatibleTransport`.

- [ ] **Step 3: Implement transport**

Create focused transport class with injected HTTP client. Do not call network in tests.

- [ ] **Step 4: Run transport tests**

Run:

```bash
pytest tests/unit/services/test_openai_transport.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/openai_transport.py tests/unit/services/test_openai_transport.py
git commit -m "feat(llm): add openai compatible transport"
```

---

## Phase 3C — Agent citation enforcement

### Task 24: Require citations for citation-bearing agents

**Files:**
- Modify: `src/de_forge/agents/base.py`
- Modify: `src/de_forge/schemas/agent_io.py`
- Test: `tests/unit/agents/test_agent_citation_policy.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/agents/test_agent_citation_policy.py`:

```python
import pytest

from de_forge.agents.base import BaseAgent, AgentOutputValidationError


class FakeLlm:
    def complete_json(self, request):
        return type("Response", (), {"content": {"confidence": 0.9}, "tokens_in": 1, "tokens_out": 1, "latency_ms": 1, "cost_usd": 0.0})()


class CitationRequiredAgent(BaseAgent):
    agent_name = "evidence"
    prompt_version = "v1"
    response_schema_name = "evidence"
    requires_citations = True

    def build_user_prompt(self, input_payload):
        return "extract evidence"


def test_citation_required_agent_rejects_empty_citations() -> None:
    agent = CitationRequiredAgent(FakeLlm(), "system")

    with pytest.raises(AgentOutputValidationError, match="citations required"):
        agent.run("run-1", ["artifact-1"], {"text": "PowerShell"})
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/unit/agents/test_agent_citation_policy.py -v
```

Expected: FAIL because BaseAgent emits empty citations.

- [ ] **Step 3: Implement citation policy**

In `BaseAgent`, add class attribute:

```python
    requires_citations: bool = False
```

Add error:

```python
class AgentOutputValidationError(ValueError):
    pass
```

Before returning envelope:

```python
        citations = response.content.get("citations", [])
        abstain = bool(response.content.get("abstain", False))
        if self.requires_citations and not abstain and not citations:
            raise AgentOutputValidationError("citations required for agent output")
```

Use `citations=citations` in envelope.

- [ ] **Step 4: Add abstain test**

Add:

```python
def test_citation_required_agent_allows_abstain_with_reason() -> None:
    class AbstainLlm:
        def complete_json(self, request):
            return type("Response", (), {"content": {"confidence": 0.1, "abstain": True, "abstain_reason": "no evidence"}, "tokens_in": 1, "tokens_out": 1, "latency_ms": 1, "cost_usd": 0.0})()

    agent = CitationRequiredAgent(AbstainLlm(), "system")

    envelope = agent.run("run-1", ["artifact-1"], {"text": ""})

    assert envelope.abstain is True
    assert envelope.abstain_reason == "no evidence"
```

- [ ] **Step 5: Run agent tests**

Run:

```bash
pytest tests/unit/agents/test_agent_citation_policy.py tests/unit/agents -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/agents/base.py src/de_forge/schemas/agent_io.py tests/unit/agents/test_agent_citation_policy.py
git commit -m "fix(agents): require citations for evidence-bearing outputs"
```

---

## Phase 4A — Metrics and readiness

### Task 25: Replace metrics table scans with aggregates

**Files:**
- Modify: `src/de_forge/services/metrics.py`
- Test: `tests/unit/services/test_metrics.py`

- [ ] **Step 1: Add regression test for aggregate truth**

In `tests/unit/services/test_metrics.py`, add or update:

```python
def test_quality_summary_uses_persisted_counts(db_session) -> None:
    # Persist proof, validation, and regression rows.
    summary = MetricsService(db_session).quality_summary()

    assert summary["sample_counts"]["proof_obligations"] == 2
    assert summary["proof_pass_rate"] == 0.5
```

- [ ] **Step 2: Run metrics tests**

Run:

```bash
pytest tests/unit/services/test_metrics.py -v
```

Expected: PASS before refactor; this pins behavior.

- [ ] **Step 3: Refactor to aggregate SQL**

Replace `.all()` calls in `MetricsService` with SQLAlchemy `select(func.count())` and grouped counts. Preserve response shape.

- [ ] **Step 4: Run metrics tests**

Run:

```bash
pytest tests/unit/services/test_metrics.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/metrics.py tests/unit/services/test_metrics.py
git commit -m "perf(metrics): use aggregate database summaries"
```

### Task 26: Add readiness endpoint

**Files:**
- Modify: `src/de_forge/main.py`
- Test: `tests/integration/api/test_readiness.py`

- [ ] **Step 1: Write failing readiness test**

Create `tests/integration/api/test_readiness.py`:

```python
from fastapi.testclient import TestClient

from de_forge.main import app


def test_ready_endpoint_reports_policy_checks() -> None:
    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert "ready" in body
    assert "checks" in body
    assert "schema" in body["checks"]
    assert "seed_routes" in body["checks"]
```

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/api/test_readiness.py -v
```

Expected: FAIL with 404.

- [ ] **Step 3: Implement `/ready`**

In `src/de_forge/main.py`, add:

```python
@app.get("/ready")
async def ready() -> dict[str, object]:
    health_payload = await health()
    checks = dict(health_payload["checks"])
    seed_routes_check = "failed" if settings.enable_dev_seed_routes and settings.env not in {"development", "test"} else "ok"
    provider_config_check = "ok" if settings.env != "production" or bool(settings.openai_api_key) else "failed"
    checks["seed_routes"] = seed_routes_check
    checks["provider_config"] = provider_config_check
    is_ready = bool(health_payload["ready"]) and seed_routes_check == "ok" and provider_config_check == "ok"
    return {"ready": is_ready, "readiness": "ready" if is_ready else "not_ready", "checks": checks, "errors": health_payload["errors"]}
```

- [ ] **Step 4: Run readiness tests**

Run:

```bash
pytest tests/integration/api/test_readiness.py tests/integration/e2e/test_sota_runtime_truth_e2e.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/main.py tests/integration/api/test_readiness.py tests/integration/e2e/test_sota_runtime_truth_e2e.py
git commit -m "feat(api): add production readiness endpoint"
```

---

## Phase 4B — Legacy cleanup and docs

### Task 27: Mark legacy review as non-authoritative

**Files:**
- Modify: `src/de_forge/api/routes/review.py`
- Test: `tests/integration/api/test_legacy_review_non_authoritative.py`

- [ ] **Step 1: Write failing test**

Create `tests/integration/api/test_legacy_review_non_authoritative.py`:

```python
def test_non_persistent_review_response_declares_not_persisted(client) -> None:
    response = client.post("/review", json={"run_id": "run-1", "rule_candidate_id": "rule-1", "action": "approve", "reviewer_notes": "ok"})

    if response.status_code != 404:
        assert response.json()["persisted"] is False
```

Use the actual legacy route path from current `review.py` tests.

- [ ] **Step 2: Run test**

Run:

```bash
pytest tests/integration/api/test_legacy_review_non_authoritative.py -v
```

Expected: FAIL if response lacks `persisted`.

- [ ] **Step 3: Add explicit non-authoritative marker**

In legacy review route response, include:

```python
"persisted": False,
"authoritative_for_export": False,
```

Do not connect this route to export gates.

- [ ] **Step 4: Run tests**

Run:

```bash
pytest tests/integration/api/test_legacy_review_non_authoritative.py tests/integration/api/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/api/routes/review.py tests/integration/api/test_legacy_review_non_authoritative.py
git commit -m "fix(review): mark legacy decisions non-authoritative"
```

### Task 28: Update operational docs

**Files:**
- Modify: `docs/operational/IMPLEMENTATION_PROGRESS.md`
- Modify: `docs/operational/CHANGELOG_AUTONOMOUS.md`
- Test: `docs/governance/preflight_checklist.md` command path

- [ ] **Step 1: Update progress doc**

Add a production-hardening section with:

```markdown
## Production Hardening Track

Source spec: `docs/superpowers/specs/2026-05-26-de-forge-production-hardening-design.md`
Plan: `docs/superpowers/plans/2026-05-26-de-forge-production-hardening-plan.md`

Layered order:
1. Bypass and invariant gate hardening.
2. Schema, evidence graph, lineage, retrieval, and review hardening.
3. PDF, LLM, and controlled-agent production wiring.
4. Operations, performance, readiness, and documentation.
```

- [ ] **Step 2: Update changelog**

Add entry:

```markdown
## 2026-05-26

- Added production-hardening implementation plan for SOTA Core v2 invariant closure.
- Planned fail-closed export eligibility, proof coverage, compiler provenance, graph lineage, PDF ingestion, LLM policy, agent citation, readiness, and metrics hardening.
```

- [ ] **Step 3: Run docs preflight**

Run the repository's documented preflight command. If it is a script, use the exact script from `docs/governance/preflight_checklist.md`.

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(ops): track production hardening plan"
```

---

## Final verification task

### Task 29: Full production-hardening verification

**Files:**
- No source changes unless verification reveals current-session regressions.

- [ ] **Step 1: Run targeted hardening tests**

```bash
pytest tests/unit/services/test_proof_coverage.py tests/unit/services/test_export_eligibility.py tests/unit/services/test_compiler_provenance.py tests/unit/services/test_evidence_graph.py tests/unit/services/test_artifact_lineage.py tests/unit/services/test_retrieval_audit_lineage.py tests/unit/services/test_schema_guard.py -v
```

Expected: PASS.

- [ ] **Step 2: Run API and E2E tests**

```bash
pytest tests/integration/api tests/integration/e2e -v
```

Expected: PASS.

- [ ] **Step 3: Run DB tests**

```bash
pytest tests/integration/db -v
```

Expected: PASS.

- [ ] **Step 4: Run unit suite**

```bash
pytest tests/unit -v
```

Expected: PASS.

- [ ] **Step 5: Run type and lint checks**

```bash
mypy src/
ruff check src/ tests/
ruff format --check src/ tests/
```

Expected: PASS.

- [ ] **Step 6: Run docs preflight**

Run the documented preflight command from `docs/governance/preflight_checklist.md`.

Expected: PASS.

- [ ] **Step 7: Commit final verification notes if docs changed**

Only commit if verification required doc updates:

```bash
git add docs/operational/IMPLEMENTATION_PROGRESS.md docs/operational/CHANGELOG_AUTONOMOUS.md
git commit -m "docs(ops): record production hardening verification"
```

---

## Self-review checklist

- Spec coverage: This plan covers seed route gating, export eligibility, proof coverage, compiler provenance, state machine hardening, evidence graph, artifact links, retrieval links, review constraints, schema guard, PDF support, LLM model policy, OpenAI-compatible transport, agent citation enforcement, aggregate metrics, readiness, legacy route cleanup, docs, and final verification.
- Placeholder scan: The plan avoids TBD/TODO placeholders. Revision IDs are intentionally represented as `<revision>` because Alembic revision IDs must be generated by the implementation environment.
- Type consistency: New services use consistent names: `ProofCoverageService`, `CompilerProvenanceService`, `ExportEligibilityService`, `EvidenceGraphService`, `ArtifactLineageService`, and `PdfTextExtractionService`.
- Scope control: The plan is phased and task-scoped. It does not introduce multi-user/RBAC/OCR/model fallback features.
