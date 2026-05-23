# DE-Forge SOTA Core v2 Validation, Oracle, and Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement static validation, rule portfolio scoring, dynamic/adversarial/counterfactual evaluation, oracle scoring, and feedback-derived regression gates for rule candidates.

**Architecture:** Rule candidates pass increasingly strict gates: static structure and broad-rule checks, dynamic positive/benign event tests, adversarial robustness tests, counterfactual condition importance, oracle expectations when present, and regression gates derived from user review feedback.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, pytest, ruff, mypy.

> **Commit policy:** Commit steps in this plan are conditional. Execute them only if the user explicitly authorizes commits for the current execution session. Otherwise skip commit commands and report changed files per task.

---

## Prerequisites

This plan starts after these plans pass:

- Foundation plan.
- Compiler plan.

Required existing files:

- `src/de_forge/schemas/sigma.py`
- `src/de_forge/services/sigma_validator.py`
- `src/de_forge/services/sigma_compiler.py`
- `src/de_forge/schemas/proof_obligation.py`

## File structure map

- `src/de_forge/schemas/rule_candidate.py` — rule candidate, score, and portfolio schemas.
- `src/de_forge/schemas/test_event.py` — normalized test event schema.
- `src/de_forge/schemas/oracle.py` — oracle case/expectation/result schemas.
- `src/de_forge/schemas/feedback.py` — review feedback schema.
- `src/de_forge/schemas/regression.py` — regression test/run schemas.
- `src/de_forge/services/portfolio_service.py` — creates candidate portfolio wrappers.
- `src/de_forge/services/static_validation.py` — static validation gates.
- `src/de_forge/services/broad_rule_detector.py` — broad-rule pattern checks.
- `src/de_forge/services/dynamic_validation.py` — positive/benign event matching.
- `src/de_forge/services/adversarial_validation.py` — adversarial variant scoring.
- `src/de_forge/services/counterfactual_evaluation.py` — condition mutation evaluation.
- `src/de_forge/services/oracle_evaluation.py` — oracle scoring.
- `src/de_forge/services/feedback_learning.py` — convert review decisions into regression patterns.
- `src/de_forge/services/regression.py` — execute regression gates.
- `tests/unit/services/test_static_validation.py`
- `tests/unit/services/test_dynamic_validation.py`
- `tests/unit/services/test_oracle_evaluation.py`
- `tests/unit/services/test_feedback_regression.py`

---

### Task 1: Rule candidate and portfolio schemas

**Files:**
- Create: `src/de_forge/schemas/rule_candidate.py`
- Create: `src/de_forge/services/portfolio_service.py`
- Test: `tests/unit/services/test_static_validation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_static_validation.py`:

```python
from de_forge.schemas.rule_candidate import CandidateScore, CandidateType, RuleCandidate
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.portfolio_service import PortfolioService


def sample_sigma_rule() -> SigmaRule:
    return SigmaRule(
        title="Suspicious Encoded PowerShell Command",
        id="rule_1",
        status="experimental",
        description="Detects encoded PowerShell command execution.",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}, "condition": "selection_1"},
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )


def test_rule_candidate_tracks_type_rule_and_score() -> None:
    candidate = RuleCandidate(
        id="candidate_1",
        detection_spec_id="spec_1",
        candidate_type=CandidateType.HIGH_PRECISION,
        sigma_rule=sample_sigma_rule(),
        score=CandidateScore(evidence_support=1.0, citation_faithfulness=1.0, telemetry_fit=1.0),
        passed_static_validation=False,
    )

    assert candidate.candidate_type == CandidateType.HIGH_PRECISION
    assert candidate.score.evidence_support == 1.0


def test_portfolio_service_wraps_sigma_rule_as_candidate() -> None:
    candidate = PortfolioService().create_candidate(
        detection_spec_id="spec_1",
        candidate_type=CandidateType.BALANCED,
        sigma_rule=sample_sigma_rule(),
    )

    assert candidate.id.startswith("candidate_")
    assert candidate.candidate_type == CandidateType.BALANCED
    assert candidate.score.citation_faithfulness == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_static_validation.py -v
```

Expected: FAIL with import error for `de_forge.schemas.rule_candidate`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/rule_candidate.py`:

```python
"""Rule candidate and portfolio scoring schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field

from de_forge.schemas.sigma import SigmaRule


class CandidateType(StrEnum):
    HIGH_PRECISION = "high_precision"
    BALANCED = "balanced"
    HIGH_RECALL = "high_recall"
    BEHAVIOR_ONLY = "behavior_only"
    IOC_ASSISTED = "ioc_assisted"
    TELEMETRY_SPECIFIC = "telemetry_specific"


class CandidateScore(BaseModel):
    evidence_support: float = Field(default=0.0, ge=0.0, le=1.0)
    citation_faithfulness: float = Field(default=0.0, ge=0.0, le=1.0)
    telemetry_fit: float = Field(default=0.0, ge=0.0, le=1.0)
    static_validity: float = Field(default=0.0, ge=0.0, le=1.0)
    dynamic_precision: float = Field(default=0.0, ge=0.0, le=1.0)
    dynamic_recall: float = Field(default=0.0, ge=0.0, le=1.0)
    adversarial_robustness: float = Field(default=0.0, ge=0.0, le=1.0)
    oracle_score: float | None = None
    regression_safety: float = Field(default=0.0, ge=0.0, le=1.0)
    false_positive_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity_penalty: float = Field(default=0.0, ge=0.0, le=1.0)


class RuleCandidate(BaseModel):
    id: str
    detection_spec_id: str
    candidate_type: CandidateType
    sigma_rule: SigmaRule
    score: CandidateScore
    passed_static_validation: bool = False
```

Create `src/de_forge/services/portfolio_service.py`:

```python
"""Create rule candidate portfolio entries."""

from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.rule_candidate import CandidateScore, CandidateType, RuleCandidate
from de_forge.schemas.sigma import SigmaRule


class PortfolioService:
    """Wrap compiled rules into typed candidates with initial scores."""

    def create_candidate(
        self,
        detection_spec_id: str,
        candidate_type: CandidateType,
        sigma_rule: SigmaRule,
    ) -> RuleCandidate:
        payload = {"spec": detection_spec_id, "type": candidate_type.value, "rule": sigma_rule.model_dump()}
        return RuleCandidate(
            id=f"candidate_{snapshot_hash(payload)[:16]}",
            detection_spec_id=detection_spec_id,
            candidate_type=candidate_type,
            sigma_rule=sigma_rule,
            score=CandidateScore(evidence_support=1.0, citation_faithfulness=1.0, telemetry_fit=1.0),
            passed_static_validation=False,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_static_validation.py -v
```

Expected: PASS, 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/rule_candidate.py src/de_forge/services/portfolio_service.py tests/unit/services/test_static_validation.py
git commit -m "feat(validation): add rule candidate portfolio schemas"
```

---

### Task 2: Static validation and broad-rule detector

**Files:**
- Create: `src/de_forge/services/broad_rule_detector.py`
- Create: `src/de_forge/services/static_validation.py`
- Modify: `tests/unit/services/test_static_validation.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/services/test_static_validation.py`:

```python
from de_forge.services.broad_rule_detector import BroadRuleDetector
from de_forge.services.static_validation import StaticValidationService


def test_broad_rule_detector_flags_single_process_name_powershell_rule() -> None:
    rule = SigmaRule(
        title="Too Broad PowerShell",
        id="rule_broad",
        status="experimental",
        description="too broad",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"Image|contains": ["powershell.exe"]}, "condition": "selection_1"},
        falsepositives=["many admin scripts"],
        level="low",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert BroadRuleDetector().is_overbroad(rule) is True


def test_static_validation_passes_precise_encoded_command_rule() -> None:
    candidate = PortfolioService().create_candidate("spec_1", CandidateType.HIGH_PRECISION, sample_sigma_rule())

    validated = StaticValidationService().validate(candidate)

    assert validated.passed_static_validation is True
    assert validated.score.static_validity == 1.0


def test_static_validation_fails_overbroad_rule() -> None:
    rule = SigmaRule(
        title="Too Broad PowerShell",
        id="rule_broad",
        status="experimental",
        description="too broad",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"Image|contains": ["powershell.exe"]}, "condition": "selection_1"},
        falsepositives=["many admin scripts"],
        level="low",
        provenance={"selection_1": ["evidence_1"]},
    )
    candidate = PortfolioService().create_candidate("spec_1", CandidateType.BALANCED, rule)

    validated = StaticValidationService().validate(candidate)

    assert validated.passed_static_validation is False
    assert validated.score.false_positive_risk == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_static_validation.py::test_broad_rule_detector_flags_single_process_name_powershell_rule -v
```

Expected: FAIL with import error for broad-rule detector.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/broad_rule_detector.py`:

```python
"""Detect overbroad detection rule patterns."""

from de_forge.schemas.sigma import SigmaRule


class BroadRuleDetector:
    """Flag simple overbroad patterns that should not become final rules."""

    def is_overbroad(self, rule: SigmaRule) -> bool:
        selection_items = [(key, value) for key, value in rule.detection.items() if key != "condition"]
        if len(selection_items) != 1:
            return False
        _, selection = selection_items[0]
        if not isinstance(selection, dict) or len(selection) != 1:
            return False
        field_expr, values = next(iter(selection.items()))
        normalized_values = [str(value).lower() for value in values] if isinstance(values, list) else [str(values).lower()]
        if field_expr.lower().startswith("image") and any("powershell" in value for value in normalized_values):
            return True
        return False
```

Create `src/de_forge/services/static_validation.py`:

```python
"""Static validation for rule candidates."""

from de_forge.schemas.rule_candidate import CandidateScore, RuleCandidate
from de_forge.services.broad_rule_detector import BroadRuleDetector
from de_forge.services.sigma_validator import SigmaValidator


class StaticValidationService:
    """Run deterministic static gates on rule candidates."""

    def __init__(self) -> None:
        self.sigma_validator = SigmaValidator()
        self.broad_rule_detector = BroadRuleDetector()

    def validate(self, candidate: RuleCandidate) -> RuleCandidate:
        structure_ok = self.sigma_validator.validate(candidate.sigma_rule)
        overbroad = self.broad_rule_detector.is_overbroad(candidate.sigma_rule)
        passed = structure_ok and not overbroad
        score = candidate.score.model_copy(
            update={
                "static_validity": 1.0 if passed else 0.0,
                "false_positive_risk": 1.0 if overbroad else candidate.score.false_positive_risk,
            }
        )
        return candidate.model_copy(update={"passed_static_validation": passed, "score": score})
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_static_validation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/broad_rule_detector.py src/de_forge/services/static_validation.py tests/unit/services/test_static_validation.py
git commit -m "feat(validation): add static validation and broad-rule checks"
```

---

### Task 3: Dynamic validation with positive and benign events

**Files:**
- Create: `src/de_forge/schemas/test_event.py`
- Create: `src/de_forge/services/dynamic_validation.py`
- Test: `tests/unit/services/test_dynamic_validation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_dynamic_validation.py`:

```python
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.schemas.test_event import TestEvent
from de_forge.services.dynamic_validation import DynamicValidationService


def encoded_rule() -> SigmaRule:
    return SigmaRule(
        title="Suspicious Encoded PowerShell Command",
        id="rule_1",
        status="experimental",
        description="Detects encoded PowerShell command execution.",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}, "condition": "selection_1"},
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )


def test_dynamic_validation_matches_positive_event() -> None:
    event = TestEvent(id="event_attack_1", fields={"CommandLine": "powershell.exe -enc AAA"}, expected_match=True)

    result = DynamicValidationService().evaluate(encoded_rule(), positive_events=[event], benign_events=[])

    assert result.true_positives == 1
    assert result.false_negatives == 0
    assert result.recall == 1.0


def test_dynamic_validation_counts_benign_false_positive() -> None:
    benign = TestEvent(id="event_benign_1", fields={"CommandLine": "powershell.exe -enc benign_admin"}, expected_match=False)

    result = DynamicValidationService().evaluate(encoded_rule(), positive_events=[], benign_events=[benign])

    assert result.false_positives == 1
    assert result.precision == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_dynamic_validation.py -v
```

Expected: FAIL with import error for `de_forge.schemas.test_event`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/test_event.py`:

```python
"""Normalized test event schemas for dynamic rule evaluation."""

from pydantic import BaseModel


class TestEvent(BaseModel):
    id: str
    fields: dict[str, str | int | float | bool]
    expected_match: bool


class DynamicValidationResult(BaseModel):
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
```

Create `src/de_forge/services/dynamic_validation.py`:

```python
"""Dynamic evaluation of Sigma-like rule conditions against normalized events."""

from de_forge.schemas.sigma import SigmaRule
from de_forge.schemas.test_event import DynamicValidationResult, TestEvent


class DynamicValidationService:
    """Evaluate simple Sigma selections against positive and benign events."""

    def evaluate(
        self,
        rule: SigmaRule,
        positive_events: list[TestEvent],
        benign_events: list[TestEvent],
    ) -> DynamicValidationResult:
        true_positives = sum(1 for event in positive_events if self._matches(rule, event))
        false_negatives = len(positive_events) - true_positives
        false_positives = sum(1 for event in benign_events if self._matches(rule, event))
        true_negatives = len(benign_events) - false_positives
        precision = true_positives / (true_positives + false_positives) if true_positives + false_positives else 0.0
        recall = true_positives / len(positive_events) if positive_events else 0.0
        return DynamicValidationResult(
            true_positives=true_positives,
            false_positives=false_positives,
            true_negatives=true_negatives,
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
        )

    def _matches(self, rule: SigmaRule, event: TestEvent) -> bool:
        for key, selection in rule.detection.items():
            if key == "condition":
                continue
            if not isinstance(selection, dict):
                continue
            if self._selection_matches(selection, event):
                return True
        return False

    def _selection_matches(self, selection: dict[str, object], event: TestEvent) -> bool:
        for field_expr, expected in selection.items():
            field, operator = self._split_field_expr(field_expr)
            observed = str(event.fields.get(field, ""))
            values = expected if isinstance(expected, list) else [expected]
            normalized_values = [str(value) for value in values]
            if operator == "contains" and not any(value in observed for value in normalized_values):
                return False
            if operator == "equals" and not any(value == observed for value in normalized_values):
                return False
        return True

    def _split_field_expr(self, field_expr: str) -> tuple[str, str]:
        if "|" not in field_expr:
            return field_expr, "equals"
        field, operator = field_expr.split("|", 1)
        return field, operator
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_dynamic_validation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/test_event.py src/de_forge/services/dynamic_validation.py tests/unit/services/test_dynamic_validation.py
git commit -m "feat(validation): add dynamic event evaluation"
```

---

### Task 4: Adversarial validation and counterfactual evaluation

**Files:**
- Create: `src/de_forge/services/adversarial_validation.py`
- Create: `src/de_forge/services/counterfactual_evaluation.py`
- Modify: `tests/unit/services/test_dynamic_validation.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/services/test_dynamic_validation.py`:

```python
from de_forge.services.adversarial_validation import AdversarialValidationService
from de_forge.services.counterfactual_evaluation import CounterfactualEvaluationService


def test_adversarial_validation_scores_variant_matches() -> None:
    variants = [
        TestEvent(id="variant_1", fields={"CommandLine": "pwsh.exe -enc AAA"}, expected_match=True),
        TestEvent(id="variant_2", fields={"CommandLine": "powershell.exe -EncodedCommand AAA"}, expected_match=True),
    ]

    result = AdversarialValidationService().evaluate(encoded_rule(), variants)

    assert result.total_variants == 2
    assert result.matched_variants == 1
    assert result.robustness_score == 0.5


def test_counterfactual_evaluation_reports_condition_importance() -> None:
    result = CounterfactualEvaluationService().evaluate_condition_importance(
        encoded_rule(),
        positive_events=[TestEvent(id="event_attack_1", fields={"CommandLine": "powershell.exe -enc AAA"}, expected_match=True)],
        benign_events=[TestEvent(id="event_benign_1", fields={"CommandLine": "powershell.exe normal"}, expected_match=False)],
    )

    assert result["selection_1"] == "important"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_dynamic_validation.py::test_adversarial_validation_scores_variant_matches -v
```

Expected: FAIL with import error for adversarial validation service.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/adversarial_validation.py`:

```python
"""Adversarial variant evaluation for rule robustness."""

from pydantic import BaseModel

from de_forge.schemas.sigma import SigmaRule
from de_forge.schemas.test_event import TestEvent
from de_forge.services.dynamic_validation import DynamicValidationService


class AdversarialValidationResult(BaseModel):
    total_variants: int
    matched_variants: int
    robustness_score: float


class AdversarialValidationService:
    """Score how many adversarial variants a rule still detects."""

    def __init__(self) -> None:
        self.dynamic = DynamicValidationService()

    def evaluate(self, rule: SigmaRule, variants: list[TestEvent]) -> AdversarialValidationResult:
        matched = sum(1 for variant in variants if self.dynamic._matches(rule, variant))
        total = len(variants)
        return AdversarialValidationResult(
            total_variants=total,
            matched_variants=matched,
            robustness_score=matched / total if total else 0.0,
        )
```

Create `src/de_forge/services/counterfactual_evaluation.py`:

```python
"""Counterfactual rule condition evaluation."""

from copy import deepcopy

from de_forge.schemas.sigma import SigmaRule
from de_forge.schemas.test_event import TestEvent
from de_forge.services.dynamic_validation import DynamicValidationService


class CounterfactualEvaluationService:
    """Estimate condition importance by removing selections and comparing recall."""

    def __init__(self) -> None:
        self.dynamic = DynamicValidationService()

    def evaluate_condition_importance(
        self,
        rule: SigmaRule,
        positive_events: list[TestEvent],
        benign_events: list[TestEvent],
    ) -> dict[str, str]:
        baseline = self.dynamic.evaluate(rule, positive_events, benign_events)
        importance: dict[str, str] = {}
        for selection_name in [key for key in rule.detection if key != "condition"]:
            mutated = deepcopy(rule)
            mutated.detection.pop(selection_name, None)
            mutated.detection["condition"] = " or ".join(key for key in mutated.detection if key != "condition")
            result = self.dynamic.evaluate(mutated, positive_events, benign_events)
            importance[selection_name] = "important" if result.recall < baseline.recall else "low"
        return importance
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_dynamic_validation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/adversarial_validation.py src/de_forge/services/counterfactual_evaluation.py tests/unit/services/test_dynamic_validation.py
git commit -m "feat(validation): add adversarial and counterfactual evaluation"
```

---

### Task 5: Oracle evaluation

**Files:**
- Create: `src/de_forge/schemas/oracle.py`
- Create: `src/de_forge/services/oracle_evaluation.py`
- Test: `tests/unit/services/test_oracle_evaluation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_oracle_evaluation.py`:

```python
from de_forge.schemas.oracle import OracleCase
from de_forge.services.oracle_evaluation import OracleEvaluationService
from tests.unit.services.test_dynamic_validation import encoded_rule


def test_oracle_evaluation_scores_expected_technique_and_telemetry() -> None:
    oracle = OracleCase(
        id="oracle_1",
        expected_techniques=["T1059.001"],
        expected_behaviors=["encoded PowerShell execution"],
        expected_telemetry=["process_creation"],
        expected_positive_event_ids=["event_attack_1"],
        must_not_match_benign_event_ids=["event_benign_1"],
        expected_logic_family=["suspicious_commandline_argument"],
    )

    result = OracleEvaluationService().evaluate(
        rule=encoded_rule(),
        oracle=oracle,
        matched_positive_event_ids=["event_attack_1"],
        matched_benign_event_ids=[],
        logic_family="suspicious_commandline_argument",
    )

    assert result.technique_score == 1.0
    assert result.telemetry_score == 1.0
    assert result.event_score == 1.0
    assert result.overall_score == 1.0


def test_oracle_evaluation_penalizes_benign_match() -> None:
    oracle = OracleCase(
        id="oracle_1",
        expected_techniques=["T1059.001"],
        expected_behaviors=["encoded PowerShell execution"],
        expected_telemetry=["process_creation"],
        expected_positive_event_ids=["event_attack_1"],
        must_not_match_benign_event_ids=["event_benign_1"],
        expected_logic_family=["suspicious_commandline_argument"],
    )

    result = OracleEvaluationService().evaluate(
        rule=encoded_rule(),
        oracle=oracle,
        matched_positive_event_ids=["event_attack_1"],
        matched_benign_event_ids=["event_benign_1"],
        logic_family="suspicious_commandline_argument",
    )

    assert result.benign_avoidance_score == 0.0
    assert result.overall_score < 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_oracle_evaluation.py -v
```

Expected: FAIL with import error for `de_forge.schemas.oracle`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/oracle.py`:

```python
"""Oracle expectations for ground-truth rule evaluation."""

from pydantic import BaseModel, Field


class OracleCase(BaseModel):
    id: str
    expected_techniques: list[str] = Field(min_length=1)
    expected_behaviors: list[str] = Field(default_factory=list)
    expected_telemetry: list[str] = Field(min_length=1)
    expected_positive_event_ids: list[str] = Field(default_factory=list)
    must_not_match_benign_event_ids: list[str] = Field(default_factory=list)
    expected_logic_family: list[str] = Field(default_factory=list)


class OracleEvaluationResult(BaseModel):
    technique_score: float
    telemetry_score: float
    event_score: float
    benign_avoidance_score: float
    logic_family_score: float
    overall_score: float
```

Create `src/de_forge/services/oracle_evaluation.py`:

```python
"""Oracle-based ground-truth evaluation."""

from de_forge.schemas.oracle import OracleCase, OracleEvaluationResult
from de_forge.schemas.sigma import SigmaRule


class OracleEvaluationService:
    """Score rule candidates against oracle expectations."""

    def evaluate(
        self,
        rule: SigmaRule,
        oracle: OracleCase,
        matched_positive_event_ids: list[str],
        matched_benign_event_ids: list[str],
        logic_family: str,
    ) -> OracleEvaluationResult:
        rule_techniques = {tag.removeprefix("attack.").upper() for tag in rule.tags if tag.startswith("attack.")}
        technique_score = 1.0 if set(oracle.expected_techniques).issubset(rule_techniques) else 0.0
        telemetry_score = 1.0 if rule.logsource.category in oracle.expected_telemetry else 0.0
        expected_positive = set(oracle.expected_positive_event_ids)
        event_score = len(expected_positive.intersection(matched_positive_event_ids)) / len(expected_positive) if expected_positive else 1.0
        forbidden = set(oracle.must_not_match_benign_event_ids)
        benign_avoidance_score = 0.0 if forbidden.intersection(matched_benign_event_ids) else 1.0
        logic_family_score = 1.0 if logic_family in oracle.expected_logic_family else 0.0
        scores = [technique_score, telemetry_score, event_score, benign_avoidance_score, logic_family_score]
        return OracleEvaluationResult(
            technique_score=technique_score,
            telemetry_score=telemetry_score,
            event_score=event_score,
            benign_avoidance_score=benign_avoidance_score,
            logic_family_score=logic_family_score,
            overall_score=sum(scores) / len(scores),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_oracle_evaluation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/oracle.py src/de_forge/services/oracle_evaluation.py tests/unit/services/test_oracle_evaluation.py
git commit -m "feat(oracle): add ground-truth oracle evaluation"
```

---

### Task 6: Feedback learning and regression gates

**Files:**
- Create: `src/de_forge/schemas/feedback.py`
- Create: `src/de_forge/schemas/regression.py`
- Create: `src/de_forge/services/feedback_learning.py`
- Create: `src/de_forge/services/regression.py`
- Test: `tests/unit/services/test_feedback_regression.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_feedback_regression.py`:

```python
import pytest

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.feedback import FeedbackDecision, ReviewFeedback
from de_forge.services.feedback_learning import FeedbackLearningService
from de_forge.services.regression import RegressionService
from tests.unit.services.test_static_validation import sample_sigma_rule


def test_rejected_feedback_becomes_do_not_repeat_regression() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )

    regression = FeedbackLearningService().to_regression_test(feedback)

    assert regression.regression_type == "do_not_repeat"
    assert regression.pattern == "powershell_process_name_only"


def test_regression_service_blocks_rejected_pattern() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )
    regression = FeedbackLearningService().to_regression_test(feedback)

    with pytest.raises(ValidationGateError):
        RegressionService([regression]).assert_candidate_safe(
            candidate_patterns=["powershell_process_name_only"],
            rule=sample_sigma_rule(),
        )


def test_regression_service_allows_candidate_without_rejected_pattern() -> None:
    feedback = ReviewFeedback(
        rule_candidate_id="candidate_1",
        decision=FeedbackDecision.REJECT,
        reason="overbroad PowerShell process-name-only rule",
        pattern="powershell_process_name_only",
    )
    regression = FeedbackLearningService().to_regression_test(feedback)

    assert RegressionService([regression]).assert_candidate_safe(
        candidate_patterns=["encoded_command_behavior"],
        rule=sample_sigma_rule(),
    ) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_feedback_regression.py -v
```

Expected: FAIL with import error for feedback schema.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/feedback.py`:

```python
"""Human review feedback schemas."""

from enum import StrEnum

from pydantic import BaseModel


class FeedbackDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"


class ReviewFeedback(BaseModel):
    rule_candidate_id: str
    decision: FeedbackDecision
    reason: str
    pattern: str
```

Create `src/de_forge/schemas/regression.py`:

```python
"""Regression gate schemas derived from review feedback."""

from pydantic import BaseModel


class RegressionTest(BaseModel):
    id: str
    regression_type: str
    pattern: str
    source_rule_candidate_id: str
    reason: str
```

Create `src/de_forge/services/feedback_learning.py`:

```python
"""Convert review feedback into regression tests."""

from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.feedback import FeedbackDecision, ReviewFeedback
from de_forge.schemas.regression import RegressionTest


class FeedbackLearningService:
    """Derive regression gates from user review feedback."""

    def to_regression_test(self, feedback: ReviewFeedback) -> RegressionTest:
        regression_type = "must_still_pass" if feedback.decision == FeedbackDecision.ACCEPT else "do_not_repeat"
        payload = feedback.model_dump()
        return RegressionTest(
            id=f"regression_{snapshot_hash(payload)[:16]}",
            regression_type=regression_type,
            pattern=feedback.pattern,
            source_rule_candidate_id=feedback.rule_candidate_id,
            reason=feedback.reason,
        )
```

Create `src/de_forge/services/regression.py`:

```python
"""Execute regression gates for candidate safety."""

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.regression import RegressionTest
from de_forge.schemas.sigma import SigmaRule


class RegressionService:
    """Check candidates against feedback-derived regression tests."""

    def __init__(self, regression_tests: list[RegressionTest]) -> None:
        self.regression_tests = regression_tests

    def assert_candidate_safe(self, candidate_patterns: list[str], rule: SigmaRule) -> bool:
        del rule
        for regression in self.regression_tests:
            if regression.regression_type == "do_not_repeat" and regression.pattern in candidate_patterns:
                raise ValidationGateError(f"candidate repeats rejected pattern {regression.pattern}")
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_feedback_regression.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/feedback.py src/de_forge/schemas/regression.py src/de_forge/services/feedback_learning.py src/de_forge/services/regression.py tests/unit/services/test_feedback_regression.py
git commit -m "feat(regression): convert feedback into regression gates"
```

---

### Task 7: Full validation/oracle/regression verification

**Files:**
- Modify only if verification finds issues.

- [ ] **Step 1: Run validation test files**

Run:

```bash
pytest tests/unit/services/test_static_validation.py tests/unit/services/test_dynamic_validation.py tests/unit/services/test_oracle_evaluation.py tests/unit/services/test_feedback_regression.py -v
```

Expected: PASS.

- [ ] **Step 2: Run all service unit tests**

Run:

```bash
pytest tests/unit/services -v
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
git commit -m "test: verify validation oracle and regression gates"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this plan:

- Rule portfolio candidate schema: Task 1.
- Static validation and overbroad rejection: Task 2.
- Dynamic positive/benign evaluation: Task 3.
- Adversarial robustness: Task 4.
- Counterfactual condition importance: Task 4.
- Oracle expectations and scoring: Task 5.
- Feedback -> regression gates: Task 6.

Deferred to later plans:

- Full orchestrator integration.
- Database persistence of validation/oracle/regression results.
- UI display of validation/proof results.
- CTI-REALM adapter.
