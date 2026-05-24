# SUPERSEDED OUTLINE — DO NOT IMPLEMENT

This outline has been replaced by the full executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-validation-oracle-regression-plan.md`

Do not use this outline for implementation. It is preserved only as historical planning context.

---

# DE-Forge SOTA Core v2 Validation, Oracle, and Regression Plan Outline

> **For agentic workers:** REQUIRED SUB-SKILL: Use the full executable validation/oracle/regression plan instead of this outline.

**Goal:** Implement static validation, dynamic/adversarial/counterfactual evaluation, oracle evaluation, and Detection CI/CD regression after compiler and rule portfolio foundations exist.

**Architecture:** Rule candidates must pass progressively stronger gates: static validity, dynamic TP/FP tests, adversarial robustness, counterfactual condition importance, oracle expectations when available, and regression gates derived from feedback.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, pytest, ruff, mypy.

---

## Prerequisites

- Foundation plan complete.
- Compiler plan complete.
- Rule portfolio plan complete.

## Static validation targets

Files:

- `src/de_forge/services/static_validation.py`
- `src/de_forge/services/broad_rule_detector.py`
- `tests/unit/services/test_static_validation.py`

Capabilities:

- Sigma syntax check.
- Field allowed check.
- Logsource compatibility check.
- ATT&CK tag validity check.
- Evidence linkage check.
- Broad-rule detection.
- Metadata completeness check.

## Dynamic/adversarial/counterfactual targets

Files:

- `src/de_forge/schemas/test_event.py`
- `src/de_forge/services/dynamic_validation.py`
- `src/de_forge/services/adversarial_validation.py`
- `src/de_forge/services/counterfactual_evaluation.py`
- `tests/unit/services/test_dynamic_validation.py`
- `tests/unit/services/test_adversarial_validation.py`
- `tests/unit/services/test_counterfactual_evaluation.py`

Capabilities:

- Positive synthetic event matching.
- Benign baseline must-not-match checks.
- Adversarial event variants.
- Rule mutation/counterfactual tests.
- Robustness score.
- Condition importance score.

## Oracle evaluation targets

Files:

- `src/de_forge/schemas/oracle.py`
- `src/de_forge/services/oracle_evaluation.py`
- `tests/unit/services/test_oracle_evaluation.py`

Capabilities:

- Expected technique checks.
- Expected behavior checks.
- Expected telemetry checks.
- Expected positive event id checks.
- Must-not-match benign event id checks.
- Expected logic family checks.
- Oracle score output.

## Feedback/regression targets

Files:

- `src/de_forge/schemas/feedback.py`
- `src/de_forge/schemas/regression.py`
- `src/de_forge/services/feedback_learning.py`
- `src/de_forge/services/regression.py`
- `tests/unit/services/test_feedback_regression.py`

Capabilities:

- Convert rejected pattern into do-not-repeat regression.
- Convert accepted rule into must-still-pass regression.
- Convert manual edit diff into preference signal.
- Regression gate checks citation mismatch, FP rate, mutation score, and coverage.

## Exit criteria

- Candidate cannot pass if overbroad.
- Candidate cannot pass if positive event is missed.
- Candidate cannot pass if must-not-match benign event is matched beyond threshold.
- Oracle score is used when oracle exists.
- Rejected patterns are blocked in future runs.
- Accepted rules remain protected by regression tests.
