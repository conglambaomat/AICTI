# SUPERSEDED OUTLINE — DO NOT IMPLEMENT

This outline has been replaced by the full executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-orchestrator-ui-dashboard-plan.md`

Do not use this outline for implementation. It is preserved only as historical planning context.

---

# DE-Forge SOTA Core v2 Orchestrator, UI, and Dashboard Plan Outline

> **For agentic workers:** REQUIRED SUB-SKILL: Use the full executable orchestrator/UI/dashboard plan instead of this outline.

**Goal:** Add end-to-end orchestration, auto/cautious modes, minimal trust-oriented Web UI, and quality dashboard after foundation, compiler, validation, oracle, agents, and regression layers are ready.

**Architecture:** The orchestrator controls every stage through explicit state transitions and hard gates. The UI exposes evidence -> graph -> DetectionSpec -> proof -> rule -> validation -> review lineage so a single user can trust and guide the system.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, pytest, httpx. Frontend stack must be chosen in a future approved UI plan.

---

## Prerequisites

- Foundation plan complete.
- Compiler plan complete.
- Portfolio/static validation plan complete.
- Dynamic/oracle/regression foundation complete.
- Controlled agents plan complete.

## Orchestrator targets

Files:

- `src/de_forge/services/state_machine.py`
- `src/de_forge/services/gates.py`
- `src/de_forge/services/orchestrator.py`
- `tests/integration/services/test_orchestrator_golden_path.py`

Capabilities:

- Explicit run states.
- Stage transition predicates.
- Bounded retry/refinement loops.
- Auto mode.
- Cautious mode.
- Abstain terminal states.
- No raw-report-to-rule bypass.

Exit criteria:

- Golden PowerShell path reaches human review in auto mode.
- Cautious mode pauses at DetectionSpec or low-confidence/proof-unknown points.
- Bounded loop limits are enforced.

## API targets

Files:

- `src/de_forge/api/routes/reports.py`
- `src/de_forge/api/routes/runs.py`
- `src/de_forge/api/routes/evidence_graph.py`
- `src/de_forge/api/routes/detection_specs.py`
- `src/de_forge/api/routes/rule_candidates.py`
- `src/de_forge/api/routes/validation.py`
- `src/de_forge/api/routes/review.py`
- `src/de_forge/api/routes/regression.py`

Capabilities:

- Upload report.
- Start run.
- Inspect run state.
- Inspect graph paths.
- Inspect DetectionSpec.
- Inspect rule portfolio.
- Inspect proof/validation.
- Submit review decision.
- Inspect regression history.

## Minimal UI targets

Pages:

- Reports.
- Run Detail.
- Evidence Graph.
- DetectionSpec.
- Rule Portfolio.
- Proof and Validation.
- Human Review.
- Regression History.

Critical UI view:

```text
Evidence quote | Detection logic | Sigma condition | Proof status | Validation score
```

Exit criteria:

- User can upload/select report.
- User can run pipeline.
- User can inspect why a rule exists.
- User can accept/reject/edit final candidate.

## Dashboard targets

Capabilities:

- Citation faithfulness trend.
- Proof pass rate.
- Static validity rate.
- Dynamic precision/recall estimates.
- Oracle score trend.
- Regression pass rate.
- Token/cost/latency trend.
- Abstain reasons.

Exit criteria:

- User can see whether system quality improves or regresses over time.
