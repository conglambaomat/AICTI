# Review Export Gate Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden DE-Forge review/export enforcement so export requires an exact approved human-review handoff and auditable persisted reviewer decision.

**Architecture:** `ReviewService` remains the deterministic policy boundary. The implementation validates review decisions before persistence, stores caller-provided audit fields, writes truthful exact-scope handoff memory, and verifies exact approved handoff before export. Existing proof-obligation and latest-decision gates remain unchanged except for stronger handoff semantics.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy ORM/Core, SQLite test database, pytest.

---

## File structure

- Modify `src/de_forge/services/review.py`: validate decisions, persist `run_id` and `comments`, write exact truthful handoff payload, and query exact approved handoff memory.
- Modify `src/de_forge/api/routes/review.py`: accept `run_id` and `comments` in persisted review decisions and pass them to `ReviewService`.
- Modify `tests/integration/services/test_review_gate.py`: add regression coverage for persisted audit fields, invalid decision rejection, rejected handoff semantics, and substring spoof blocking.
- Modify `tests/e2e/test_api_review_and_export.py`: keep existing API/export behavior green; add invalid review decision API coverage only if needed after service/API validation.

## Task 1: Add failing service tests for review audit persistence and decision validation

**Files:**
- Modify: `tests/integration/services/test_review_gate.py:33-73`
- Test: `tests/integration/services/test_review_gate.py`

- [ ] **Step 1: Write failing tests**

Add these imports near the top of `tests/integration/services/test_review_gate.py`:

```python
import json

from sqlalchemy import text
```

Add these tests after `test_append_only_review_decisions`:

```python
def test_review_decision_persists_run_id_and_comments() -> None:
    db = _build_session()
    service = ReviewService(db)

    decision_id = service.record_decision(
        rule_id="rule-audit-fields",
        run_id="run-audit-fields",
        decision="approved",
        reviewer="analyst@example.com",
        comments="Evidence and proof obligations reviewed.",
    )

    row = db.query(ReviewDecisionModel).filter_by(id=decision_id).one()
    assert row.rule_id == "rule-audit-fields"
    assert row.run_id == "run-audit-fields"
    assert row.decision == "approved"
    assert row.reviewer == "analyst@example.com"
    assert row.comments == "Evidence and proof obligations reviewed."


def test_invalid_review_decision_is_rejected_before_persistence() -> None:
    db = _build_session()
    service = ReviewService(db)

    with pytest.raises(ValueError, match="invalid review decision"):
        service.record_decision(
            rule_id="rule-invalid-decision",
            run_id="run-invalid-decision",
            decision="maybe",
            reviewer="analyst@example.com",
            comments="Invalid decision must not persist.",
        )

    rows = db.query(ReviewDecisionModel).filter_by(rule_id="rule-invalid-decision").all()
    assert rows == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py::test_review_decision_persists_run_id_and_comments tests/integration/services/test_review_gate.py::test_invalid_review_decision_is_rejected_before_persistence -q
```

Expected: FAIL because `ReviewService.record_decision()` does not accept `run_id` or `comments`, and it does not validate decision values.

- [ ] **Step 3: Implement minimal service support**

In `src/de_forge/services/review.py`, add a module-level allowed decision set after `ExportBlockedError`:

```python
ALLOWED_REVIEW_DECISIONS = {"approved", "rejected"}
```

Change the `record_decision` signature and payload construction in `src/de_forge/services/review.py` to:

```python
    def record_decision(
        self,
        rule_id: str,
        decision: str,
        reviewer: str,
        run_id: str = "run_unknown",
        comments: str = "",
    ) -> str:
        """Record append-only review decision for a rule."""
        if decision not in ALLOWED_REVIEW_DECISIONS:
            raise ValueError(f"invalid review decision: {decision}")

        db = self._require_db()
        decision_id = str(uuid4())
        created_at = datetime.fromtimestamp(time_ns() / 1_000_000_000, tz=UTC).isoformat()
        bind = db.get_bind()
        columns = {column["name"] for column in inspect(bind).get_columns("review_decisions")}
        payload: dict[str, str] = {
            "id": decision_id,
            "rule_id": rule_id,
            "decision": decision,
            "reviewer": reviewer,
            "created_at": created_at,
        }
        if "run_id" in columns:
            payload["run_id"] = run_id
        if "comments" in columns:
            payload["comments"] = comments
```

Do not change handoff behavior in this task beyond what is necessary to keep existing tests compiling.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py::test_review_decision_persists_run_id_and_comments tests/integration/services/test_review_gate.py::test_invalid_review_decision_is_rejected_before_persistence -q
```

Expected: PASS.

- [ ] **Step 5: Run affected review tests**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit task**

Run:

```bash
git add src/de_forge/services/review.py tests/integration/services/test_review_gate.py
git commit -m "$(cat <<'EOF'
fix(review): persist audited decision fields

Preserve reviewer-provided run context and comments while rejecting invalid review decisions before persistence.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

## Task 2: Add failing service tests for exact truthful handoff enforcement

**Files:**
- Modify: `tests/integration/services/test_review_gate.py:48-73`
- Modify: `src/de_forge/services/review.py:63-170`
- Test: `tests/integration/services/test_review_gate.py`

- [ ] **Step 1: Write failing tests**

Add these tests after `test_export_allowed_after_latest_approval`:

```python
def test_rejected_decision_writes_non_approved_handoff_and_blocks_export() -> None:
    db = _build_session()
    service = ReviewService(db)

    rule_id = "rule-rejected-handoff"
    service.record_decision(
        rule_id=rule_id,
        run_id="run-rejected-handoff",
        decision="rejected",
        reviewer="analyst@example.com",
        comments="Too broad.",
    )

    value = db.execute(
        text("SELECT value FROM memory_views WHERE scope = :scope AND key = 'latest'"),
        {"scope": f"{rule_id}:review.handoff"},
    ).scalar_one()
    payload = json.loads(value)
    assert payload["approved"] is False
    assert payload["decision"] == "rejected"
    assert payload["reviewer"] == "analyst@example.com"

    with pytest.raises(ExportBlockedError, match="review handoff memory required"):
        service.assert_can_export(rule_id=rule_id, rule_status="awaiting_review")


def test_review_handoff_requires_exact_rule_scope_not_substring() -> None:
    db = _build_session()
    service = ReviewService(db)

    target_rule_id = "rule-1"
    other_rule_id = "prefix-rule-1-suffix"
    service.record_decision(
        rule_id=target_rule_id,
        run_id="run-target",
        decision="approved",
        reviewer="target@example.com",
        comments="Target has approval but no handoff after deletion.",
    )
    service.record_decision(
        rule_id=other_rule_id,
        run_id="run-other",
        decision="approved",
        reviewer="other@example.com",
        comments="Other rule approval must not satisfy target.",
    )
    db.execute(
        text("DELETE FROM memory_views WHERE scope = :scope AND key = 'latest'"),
        {"scope": f"{target_rule_id}:review.handoff"},
    )
    db.commit()

    with pytest.raises(ExportBlockedError, match="review handoff memory required"):
        service.assert_can_export(rule_id=target_rule_id, rule_status="awaiting_review")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py::test_rejected_decision_writes_non_approved_handoff_and_blocks_export tests/integration/services/test_review_gate.py::test_review_handoff_requires_exact_rule_scope_not_substring -q
```

Expected: FAIL because handoff payload is always approved and substring scope matching allows spoofed handoff.

- [ ] **Step 3: Implement exact truthful handoff memory**

In `src/de_forge/services/review.py`, add JSON import near the top:

```python
import json
```

Replace the memory insert payload inside `record_decision` with:

```python
            db.execute(
                text(
                    """
                    INSERT INTO memory_views (id, scope, key, value, updated_at)
                    VALUES (:id, :scope, 'latest', :value, :updated_at)
                    """
                ),
                {
                    "id": f"mv-{decision_id}",
                    "scope": self._review_handoff_scope(rule_id),
                    "value": json.dumps(
                        {
                            "approved": decision == "approved",
                            "decision": decision,
                            "decision_id": decision_id,
                            "reviewer": reviewer,
                            "run_id": run_id,
                        },
                        sort_keys=True,
                    ),
                    "updated_at": created_at,
                },
            )
```

Add this helper method before `_has_review_handoff_memory`:

```python
    def _review_handoff_scope(self, rule_id: str) -> str:
        return f"{rule_id}:review.handoff"
```

Replace `_has_review_handoff_memory` with:

```python
    def _has_review_handoff_memory(self, rule_id: str) -> bool:
        db = self._require_db()
        value = db.execute(
            text("SELECT value FROM memory_views WHERE scope = :scope AND key = 'latest'"),
            {"scope": self._review_handoff_scope(rule_id)},
        ).scalar_one_or_none()
        if value is None:
            return False

        try:
            payload = json.loads(str(value))
        except json.JSONDecodeError:
            return False

        return payload.get("approved") is True and payload.get("decision") == "approved"
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py::test_rejected_decision_writes_non_approved_handoff_and_blocks_export tests/integration/services/test_review_gate.py::test_review_handoff_requires_exact_rule_scope_not_substring -q
```

Expected: PASS.

- [ ] **Step 5: Run affected review gate tests**

Run:

```bash
python -m pytest tests/integration/services/test_review_gate.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit task**

Run:

```bash
git add src/de_forge/services/review.py tests/integration/services/test_review_gate.py
git commit -m "$(cat <<'EOF'
fix(review): require exact approved handoff

Block export unless review handoff memory exactly matches the reviewed rule and records an approved human decision.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

## Task 3: Wire persisted review API audit fields

**Files:**
- Modify: `src/de_forge/api/routes/review.py:13-33`
- Modify: `tests/e2e/test_api_review_and_export.py`
- Test: `tests/e2e/test_api_review_and_export.py`

- [ ] **Step 1: Write failing API test**

Add this test after `test_post_review_rejection` in `tests/e2e/test_api_review_and_export.py`:

```python
def test_post_review_rejects_invalid_decision() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "maybe",
            "comments": "Invalid review decision.",
        },
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/e2e/test_api_review_and_export.py::test_post_review_rejects_invalid_decision -q
```

Expected: FAIL if the API currently accepts invalid decision strings or returns a non-422 response.

- [ ] **Step 3: Implement API request validation and field pass-through**

In `src/de_forge/api/routes/review.py`, add this import:

```python
from typing import Literal
```

Change `ReviewDecisionRequest` to:

```python
class ReviewDecisionRequest(BaseModel):
    rule_id: str
    run_id: str
    decision: Literal["approved", "rejected"]
    reviewer: str
    comments: str = ""
```

Change `record_decision` call to:

```python
    decision_id = service.record_decision(
        rule_id=request.rule_id,
        run_id=request.run_id,
        decision=request.decision,
        reviewer=request.reviewer,
        comments=request.comments,
    )
```

- [ ] **Step 4: Run API test to verify it passes**

Run:

```bash
python -m pytest tests/e2e/test_api_review_and_export.py::test_post_review_rejects_invalid_decision -q
```

Expected: PASS.

- [ ] **Step 5: Run e2e review/export tests**

Run:

```bash
python -m pytest tests/e2e/test_api_review_and_export.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit task**

Run:

```bash
git add src/de_forge/api/routes/review.py tests/e2e/test_api_review_and_export.py
git commit -m "$(cat <<'EOF'
fix(api): validate persisted review decisions

Require review API callers to provide run context and a valid human review decision before persistence.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

## Task 4: Final verification and scope audit

**Files:**
- Verify only; do not modify files unless a prior task left tests failing.

- [ ] **Step 1: Run targeted review/export verification**

Run:

```bash
python -m pytest tests/unit/services/test_review_service.py tests/integration/services/test_review_gate.py tests/e2e/test_api_review_and_export.py -q
```

Expected: PASS.

- [ ] **Step 2: Run schema/docs regression verification**

Run:

```bash
python -m pytest tests/integration/db tests/docs/test_manifest_freeze.py tests/docs/test_docs_preflight.py tests/docs/test_docs_references.py tests/docs/test_progress_templates.py -q
```

Expected: PASS.

- [ ] **Step 3: Run docs preflight**

Run:

```bash
python scripts/docs_preflight.py
```

Expected output includes:

```text
DOCS_PREFLIGHT: PASS
```

- [ ] **Step 4: Inspect git status**

Run:

```bash
git status --short
```

Expected: only known pre-existing untracked local artifacts may remain, such as `.claude/worktrees/` and `de_forge.db`. No uncommitted source/test changes should remain from this plan.

- [ ] **Step 5: Commit any verification-only doc update only if one was required**

If no files changed during final verification, do not create an empty commit. If a small correction was required, commit only the affected files with:

```bash
git add <affected-files>
git commit -m "$(cat <<'EOF'
fix(review): complete review export gate hardening

Finalize review/export gate hardening after targeted verification.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

## Self-review

- Spec coverage: Tasks cover exact handoff identity, truthful handoff payload, persisted run_id/comments, invalid decision rejection, append-only semantics, proof gate preservation, and regression tests.
- Placeholder scan: No TBD/TODO/fill-in steps remain. Each code-changing step includes exact code and exact file paths.
- Type consistency: `record_decision(rule_id, decision, reviewer, run_id="run_unknown", comments="")` remains backward-compatible for existing service tests while allowing API pass-through. API uses `Literal["approved", "rejected"]`, matching `ALLOWED_REVIEW_DECISIONS`.
