# Evidence Citation Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make evidence span persistence fail closed unless each persisted quote exactly matches the persisted report chunk text at the submitted global offsets.

**Architecture:** `EvidenceAgentService` keeps its existing retrieval-grounded, chunk-relative extraction filtering. `EvidenceService` becomes the final deterministic persistence gate by converting global evidence offsets to chunk-relative offsets and verifying the exact quote against `ReportChunk.chunk_text` before any `EvidenceSpan` is inserted. Existing database constraints remain as structural backstops, while service validation provides the semantic citation guarantee.

**Tech Stack:** Python 3.11, SQLAlchemy ORM, pytest, SQLite in-memory integration tests, existing `EvidenceService`, existing `verify_citation` helper.

---

## File Structure

- Modify `tests/integration/services/test_evidence_service.py`
  - Add failing persistence tests for exact quote verification at global offsets.
  - Add fail-closed tests for quote mismatch, zero-length spans, and rollback/no partial persistence.
  - Preserve existing lineage and non-zero chunk offset coverage.
- Modify `src/de_forge/services/evidence.py`
  - Import and use `verify_citation` at the persistence boundary.
  - Convert global offsets to chunk-relative offsets with `relative_start = ev.char_start - chunk.char_start` and `relative_end = ev.char_end - chunk.char_start`.
  - Raise `EvidenceExtractionError` on invalid offsets or exact quote mismatch before commit.
- Verify `tests/integration/services/test_evidence_agent.py`
  - Run existing agent extraction tests to prove retrieval-grounded chunk-relative behavior is unchanged.
- Verify `tests/unit/services/test_chunking_citation.py`
  - Run existing citation helper unit tests because `EvidenceService` will depend on that helper.

---

### Task 1: Reject persisted evidence when quote does not match persisted chunk text

**Files:**
- Modify: `tests/integration/services/test_evidence_service.py`
- Modify: `src/de_forge/services/evidence.py`

- [ ] **Step 1: Write the failing mismatch test**

Append this test after `test_evidence_with_nonzero_chunk_start_validates_absolute_offsets` in `tests/integration/services/test_evidence_service.py`:

```python
def test_evidence_quote_must_match_persisted_chunk_text_at_absolute_offsets() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(
        db, chunk_text="attacker launched powershell -enc abc", chunk_char_start=40
    )
    service = EvidenceService(db)

    with pytest.raises(EvidenceExtractionError, match="quote does not match chunk text"):
        service.persist_evidence(
            report_id=report_id,
            run_id="run-mismatch",
            created_by_agent="evidence-agent",
            evidence=[
                EvidenceInput(
                    evidence_id="evidence-mismatch",
                    chunk_id=chunk_id,
                    quote="cmd.exe /c whoami",
                    char_start=58,
                    char_end=73,
                    supports_claim="Encoded PowerShell execution observed",
                    confidence=0.91,
                )
            ],
        )

    persisted = (
        db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    )
    assert persisted == []
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py::test_evidence_quote_must_match_persisted_chunk_text_at_absolute_offsets -q
```

Expected: FAIL because current `EvidenceService._validate_evidence_span` only checks offset bounds and accepts a quote that does not equal `ReportChunk.chunk_text[relative_start:relative_end]`.

- [ ] **Step 3: Implement exact quote validation in `EvidenceService`**

In `src/de_forge/services/evidence.py`, add the import:

```python
from de_forge.services.citation_verifier import verify_citation
```

Then extend `_validate_evidence_span` after the existing chunk bound checks:

```python
        relative_start = ev.char_start - chunk.char_start
        relative_end = ev.char_end - chunk.char_start
        try:
            quote_matches = verify_citation(
                chunk.chunk_text, ev.quote, relative_start, relative_end
            )
        except ValueError as exc:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: invalid citation offsets for chunk {ev.chunk_id}"
            ) from exc
        if not quote_matches:
            raise EvidenceExtractionError(
                f"Evidence {ev.evidence_id}: quote does not match chunk text at char_start={ev.char_start}, char_end={ev.char_end}"
            )
```

Do not change `EvidenceAgentService.extract()` in this task.

- [ ] **Step 4: Run the mismatch test to verify it passes**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py::test_evidence_quote_must_match_persisted_chunk_text_at_absolute_offsets -q
```

Expected: PASS.

- [ ] **Step 5: Run affected evidence persistence tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/evidence.py tests/integration/services/test_evidence_service.py
git commit -m "fix(evidence): verify persisted quote citations

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Preserve exact-match persistence for non-zero global offsets

**Files:**
- Modify: `tests/integration/services/test_evidence_service.py`
- Modify: `src/de_forge/services/evidence.py`

- [ ] **Step 1: Strengthen the existing non-zero offset test**

In `tests/integration/services/test_evidence_service.py`, update `test_evidence_with_nonzero_chunk_start_validates_absolute_offsets` so the quote and offsets prove the service converts global offsets to chunk-relative offsets correctly:

```python
def test_evidence_with_nonzero_chunk_start_validates_absolute_offsets() -> None:
    """Evidence offsets are absolute and must stay within non-zero chunk bounds."""
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(
        db, chunk_text="prefix powershell -enc abc suffix", chunk_char_start=100
    )
    service = EvidenceService(db)

    result = service.persist_evidence(
        report_id=report_id,
        run_id="run-3",
        created_by_agent="evidence-agent",
        evidence=[
            EvidenceInput(
                evidence_id="evidence-2",
                chunk_id=chunk_id,
                quote="powershell -enc",
                char_start=107,
                char_end=122,
                supports_claim="PowerShell execution detected",
                confidence=0.88,
            )
        ],
    )

    assert result == ["evidence-2"]

    persisted = db.execute(select(EvidenceSpan).where(EvidenceSpan.id == "evidence-2")).scalar_one()
    assert persisted.quote == "powershell -enc"
    assert persisted.char_start == 107
    assert persisted.char_end == 122
    assert persisted.chunk_id == chunk_id
```

- [ ] **Step 2: Run the strengthened test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py::test_evidence_with_nonzero_chunk_start_validates_absolute_offsets -q
```

Expected: PASS after Task 1. If it fails, fix only the global-to-relative offset conversion in `EvidenceService._validate_evidence_span`.

- [ ] **Step 3: Add a zero-length span rejection test**

Append this test in `tests/integration/services/test_evidence_service.py`:

```python
def test_evidence_rejects_zero_length_span_even_when_quote_is_non_empty() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(db)
    service = EvidenceService(db)

    with pytest.raises(EvidenceExtractionError, match="quote does not match chunk text"):
        service.persist_evidence(
            report_id=report_id,
            run_id="run-zero-length",
            created_by_agent="evidence-agent",
            evidence=[
                EvidenceInput(
                    evidence_id="evidence-zero-length",
                    chunk_id=chunk_id,
                    quote="powershell",
                    char_start=0,
                    char_end=0,
                    supports_claim="PowerShell execution detected",
                    confidence=0.8,
                )
            ],
        )

    persisted = (
        db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    )
    assert persisted == []
```

This locks the current contract that `char_end == char_start` passes the database shape constraint but must fail the semantic quote-match gate unless the quote is empty, which is already rejected earlier.

- [ ] **Step 4: Run targeted tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py::test_evidence_with_nonzero_chunk_start_validates_absolute_offsets tests/integration/services/test_evidence_service.py::test_evidence_rejects_zero_length_span_even_when_quote_is_non_empty -q
```

Expected: PASS.

- [ ] **Step 5: Run evidence persistence suite**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/de_forge/services/evidence.py tests/integration/services/test_evidence_service.py
git commit -m "test(evidence): lock global citation offsets

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Prove batch persistence rolls back on any invalid citation

**Files:**
- Modify: `tests/integration/services/test_evidence_service.py`
- Modify: `src/de_forge/services/evidence.py` only if the test exposes partial persistence

- [ ] **Step 1: Write rollback test for mixed valid and invalid evidence**

Append this test in `tests/integration/services/test_evidence_service.py`:

```python
def test_evidence_batch_rolls_back_when_any_quote_mismatches() -> None:
    db = _build_session()
    report_id, chunk_id = _seed_report_and_chunk(
        db, chunk_text="first behavior second behavior", chunk_char_start=10
    )
    service = EvidenceService(db)

    with pytest.raises(EvidenceExtractionError, match="quote does not match chunk text"):
        service.persist_evidence(
            report_id=report_id,
            run_id="run-batch-mismatch",
            created_by_agent="evidence-agent",
            evidence=[
                EvidenceInput(
                    evidence_id="evidence-valid-before-invalid",
                    chunk_id=chunk_id,
                    quote="first behavior",
                    char_start=10,
                    char_end=24,
                    supports_claim="First behavior observed",
                    confidence=0.9,
                ),
                EvidenceInput(
                    evidence_id="evidence-invalid-after-valid",
                    chunk_id=chunk_id,
                    quote="unrelated behavior",
                    char_start=25,
                    char_end=40,
                    supports_claim="Second behavior observed",
                    confidence=0.9,
                ),
            ],
        )

    persisted = (
        db.execute(select(EvidenceSpan).where(EvidenceSpan.report_id == report_id)).scalars().all()
    )
    assert persisted == []
```

- [ ] **Step 2: Run rollback test**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py::test_evidence_batch_rolls_back_when_any_quote_mismatches -q
```

Expected: PASS after Task 1 because `persist_evidence` validates all spans before adding any `EvidenceSpan`. If it fails due partial persistence, move validation before insertion and keep one commit boundary.

- [ ] **Step 3: Run full evidence service tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/de_forge/services/evidence.py tests/integration/services/test_evidence_service.py
git commit -m "test(evidence): fail closed evidence batches

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If Step 2 and Step 3 pass with test-only changes, commit only `tests/integration/services/test_evidence_service.py`.

---

### Task 4: Preserve existing evidence agent extraction behavior

**Files:**
- Verify: `tests/integration/services/test_evidence_agent.py`
- Verify: `tests/unit/services/test_chunking_citation.py`
- Verify: `src/de_forge/services/evidence.py`

- [ ] **Step 1: Run existing evidence agent tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_agent.py -q
```

Expected: PASS. This proves `EvidenceAgentService.extract()` still accepts grounded chunk-relative quotes and abstains when no grounded evidence exists.

- [ ] **Step 2: Run citation helper tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/unit/services/test_chunking_citation.py -q
```

Expected: PASS. This proves the helper used by persistence still accepts exact offsets and rejects mismatches/out-of-bounds offsets.

- [ ] **Step 3: Run combined evidence tests**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py tests/integration/services/test_evidence_agent.py tests/unit/services/test_chunking_citation.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit only if verification required a fix**

If verification exposes a regression caused by this phase, fix only the regression and commit related files:

```bash
git add src/de_forge/services/evidence.py tests/integration/services/test_evidence_service.py tests/integration/services/test_evidence_agent.py tests/unit/services/test_chunking_citation.py
git commit -m "fix(evidence): preserve grounded extraction behavior

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

### Task 5: Phase verification and audit

**Files:**
- Verify only: no required source modifications.

- [ ] **Step 1: Run full affected evidence test set**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/services/test_evidence_service.py tests/integration/services/test_evidence_agent.py tests/unit/services/test_chunking_citation.py -q
```

Expected: PASS.

- [ ] **Step 2: Run broader evidence/citation regression selection**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration -q -k "evidence or citation"
```

Expected: PASS or no unrelated failures. If failures occur, fix only failures caused by this phase.

- [ ] **Step 3: Run schema/migration regression backstop**

Run:

```bash
PYTHONPATH="$PWD/src" python -m pytest tests/integration/db/test_migrations_contract.py tests/integration/db/test_schema_contract.py -q
```

Expected: PASS. This confirms the service-only hardening did not require schema drift.

- [ ] **Step 4: Run docs preflight**

Run:

```bash
PYTHONPATH="$PWD/src" python scripts/docs_preflight.py
```

Expected: `DOCS_PREFLIGHT: PASS`.

- [ ] **Step 5: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no whitespace errors in phase files. A CRLF warning for unrelated `.claude/settings.local.json` is not a phase failure and must not be staged.

- [ ] **Step 6: Review commit boundary**

Run:

```bash
git status --short
git diff --stat
```

Expected: only Phase 3 files are modified. Do not stage or commit local artifacts such as `de_forge.db`, `.claude/settings.local.json`, `.claude/scheduled_tasks.lock`, `.claude/worktrees/`, `.env`, cache files, or unrelated docs.

- [ ] **Step 7: Commit only if verification produced tracked fixes**

If verification required fixes, commit only related phase files:

```bash
git add <related phase files>
git commit -m "fix(evidence): complete citation hardening verification

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

If no files changed, do not create an empty commit.

---

## Self-Review

**Spec coverage:**
- Evidence span persistence fails closed on exact quote mismatch using persisted `ReportChunk.chunk_text`: Task 1.
- Global offsets are interpreted correctly against chunk text using `chunk.char_start`: Task 2.
- Offset bounds and zero-length semantic mismatch are covered: Task 2.
- Persistence/audit behavior and rollback/no partial persistence are covered: Task 1 and Task 3.
- Existing evidence agent extraction behavior is preserved and verified without modifying `EvidenceAgentService.extract()`: Task 4.
- Phase-level regression checks are defined: Task 5.

**Placeholder scan:** No TODO/TBD/placeholders remain. Every code change step includes concrete code and exact commands.

**Type consistency:** `EvidenceInput.char_start` and `EvidenceInput.char_end` remain global offsets. `verify_citation(text, quote, start_offset, end_offset)` receives chunk-local offsets derived from persisted `ReportChunk.char_start`. `EvidenceService.persist_evidence(...)` and `EvidenceAgentService.extract(...)` public signatures are unchanged.

**Scope control:** This phase does not change retrieval persistence, DetectionSpec generation, ATT&CK mapping, rule generation, proof obligation logic, review/export behavior, schema migrations, or API routes. It only hardens the deterministic evidence persistence boundary.
