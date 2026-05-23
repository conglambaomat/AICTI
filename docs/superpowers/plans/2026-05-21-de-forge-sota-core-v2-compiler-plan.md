# DE-Forge SOTA Core v2 Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Detection AST, Sigma AST, and deterministic Sigma compiler so verified DetectionSpecs produce Sigma candidates without relying on free-form YAML generation.

**Architecture:** DetectionSpec logic requirements are converted into a typed Detection AST, then into a Sigma rule object, then serialized to YAML. The compiler validates telemetry/logsource compatibility, rejects unsupported fields, and preserves provenance from Sigma conditions back to evidence ids.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, pytest, ruff, mypy.

> **Commit policy:** Commit steps in this plan are conditional. Execute them only if the user explicitly authorizes commits for the current execution session. Otherwise skip commit commands and report changed files per task.

---

## Prerequisites

This plan starts only after the foundation plan passes. Required existing files from foundation:

- `src/de_forge/schemas/detection_spec.py`
- `src/de_forge/services/detection_spec_verifier.py`
- `src/de_forge/services/telemetry_registry.py`
- `src/de_forge/core/errors.py`

## File structure map

- `src/de_forge/schemas/detection_ast.py` — typed rule logic AST.
- `src/de_forge/schemas/sigma.py` — typed Sigma rule representation.
- `src/de_forge/services/detection_ast_service.py` — converts verified DetectionSpec to Detection AST.
- `src/de_forge/services/sigma_compiler.py` — compiles Detection AST into Sigma rule object/YAML.
- `src/de_forge/services/sigma_validator.py` — validates Sigma structure, fields, and condition references.
- `tests/unit/services/test_detection_ast.py` — AST conversion tests.
- `tests/unit/services/test_sigma_compiler.py` — compiler and validator tests.

---

### Task 1: Detection AST schema

**Files:**
- Create: `src/de_forge/schemas/detection_ast.py`
- Test: `tests/unit/services/test_detection_ast.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_detection_ast.py`:

```python
from de_forge.schemas.detection_ast import FieldConditionNode, LogicGroupNode, LogicOperator


def test_field_condition_node_tracks_evidence_ids() -> None:
    node = FieldConditionNode(
        id="cond_1",
        field="CommandLine",
        operator="contains_any",
        values=["-enc", "-EncodedCommand"],
        evidence_ids=["evidence_1"],
    )

    assert node.field == "CommandLine"
    assert node.evidence_ids == ["evidence_1"]


def test_logic_group_node_contains_child_conditions() -> None:
    condition = FieldConditionNode(
        id="cond_1",
        field="CommandLine",
        operator="contains_any",
        values=["-enc"],
        evidence_ids=["evidence_1"],
    )
    group = LogicGroupNode(id="group_1", operator=LogicOperator.ALL, children=[condition])

    assert group.operator == LogicOperator.ALL
    assert group.children[0].id == "cond_1"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_detection_ast.py -v
```

Expected: FAIL with import error for `de_forge.schemas.detection_ast`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/detection_ast.py`:

```python
"""Typed Detection AST used as the source for rule compilation."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class LogicOperator(StrEnum):
    ALL = "all"
    ANY = "any"
    NOT = "not"


class FieldConditionNode(BaseModel):
    id: str
    node_type: Literal["field_condition"] = "field_condition"
    field: str
    operator: str
    values: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class LogicGroupNode(BaseModel):
    id: str
    node_type: Literal["logic_group"] = "logic_group"
    operator: LogicOperator
    children: list[FieldConditionNode] = Field(min_length=1)


class DetectionAst(BaseModel):
    id: str
    detection_spec_id: str
    root: LogicGroupNode
    telemetry_source_id: str
    attack_techniques: list[str]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_detection_ast.py -v
```

Expected: PASS, 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/detection_ast.py tests/unit/services/test_detection_ast.py
git commit -m "feat(compiler): add detection AST schema"
```

---

### Task 2: Convert verified DetectionSpec to Detection AST

**Files:**
- Create: `src/de_forge/services/detection_ast_service.py`
- Modify: `tests/unit/services/test_detection_ast.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/services/test_detection_ast.py`:

```python
from de_forge.schemas.detection_spec import DetectionCondition, DetectionSpec, TelemetryRequirement
from de_forge.services.detection_ast_service import DetectionAstService


def test_detection_ast_service_converts_verified_spec_to_ast() -> None:
    spec = DetectionSpec(
        id="spec_1",
        evidence_ids=["evidence_1"],
        behavior_ids=["behavior_1"],
        attack_techniques=["T1059.001"],
        detection_strategies=["ds_command_line_behavior"],
        analytics=["analytic_encoded_powershell"],
        data_components=["process_creation"],
        telemetry_requirements=[TelemetryRequirement(source_id="sysmon_eid_1", required_fields=["CommandLine"])],
        allowed_fields=["CommandLine"],
        logic_requirements=[
            DetectionCondition(
                field="CommandLine",
                operator="contains_any",
                values=["-enc", "-EncodedCommand"],
                evidence_ids=["evidence_1"],
            )
        ],
        false_positive_hypotheses=["admin encoded PowerShell"],
        test_plan=["positive encoded command", "benign PowerShell"],
        verified=True,
    )

    ast = DetectionAstService().from_spec(spec)

    assert ast.detection_spec_id == "spec_1"
    assert ast.telemetry_source_id == "sysmon_eid_1"
    assert ast.root.children[0].field == "CommandLine"
    assert ast.attack_techniques == ["T1059.001"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_detection_ast.py::test_detection_ast_service_converts_verified_spec_to_ast -v
```

Expected: FAIL with import error for `de_forge.services.detection_ast_service`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/detection_ast_service.py`:

```python
"""Build Detection ASTs from verified DetectionSpecs."""

from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.detection_ast import DetectionAst, FieldConditionNode, LogicGroupNode, LogicOperator
from de_forge.schemas.detection_spec import DetectionSpec


class DetectionAstService:
    """Convert verified DetectionSpecs into compiler-friendly ASTs."""

    def from_spec(self, spec: DetectionSpec) -> DetectionAst:
        if not spec.verified:
            raise ValidationGateError("DetectionSpec must be verified before AST generation")
        if not spec.telemetry_requirements:
            raise ValidationGateError("DetectionSpec requires telemetry before AST generation")

        children = [
            FieldConditionNode(
                id=f"cond_{snapshot_hash(condition.model_dump())[:12]}",
                field=condition.field,
                operator=condition.operator,
                values=condition.values,
                evidence_ids=condition.evidence_ids,
            )
            for condition in spec.logic_requirements
        ]
        root = LogicGroupNode(id=f"group_{snapshot_hash(spec.id)[:12]}", operator=LogicOperator.ALL, children=children)
        return DetectionAst(
            id=f"ast_{snapshot_hash(spec.model_dump())[:16]}",
            detection_spec_id=spec.id,
            root=root,
            telemetry_source_id=spec.telemetry_requirements[0].source_id,
            attack_techniques=spec.attack_techniques,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_detection_ast.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/detection_ast_service.py tests/unit/services/test_detection_ast.py
git commit -m "feat(compiler): build detection AST from verified specs"
```

---

### Task 3: Sigma rule schema

**Files:**
- Create: `src/de_forge/schemas/sigma.py`
- Test: `tests/unit/services/test_sigma_compiler.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/services/test_sigma_compiler.py`:

```python
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule


def test_sigma_rule_schema_tracks_detection_and_provenance() -> None:
    rule = SigmaRule(
        title="Suspicious Encoded PowerShell Command",
        id="rule_1",
        status="experimental",
        description="Detects encoded PowerShell command execution.",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation", service=None),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}, "condition": "selection_1"},
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert rule.logsource.category == "process_creation"
    assert rule.provenance["selection_1"] == ["evidence_1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py -v
```

Expected: FAIL with import error for `de_forge.schemas.sigma`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/schemas/sigma.py`:

```python
"""Typed Sigma rule representation."""

from typing import Any

from pydantic import BaseModel, Field


class SigmaLogsource(BaseModel):
    product: str
    category: str
    service: str | None = None


class SigmaRule(BaseModel):
    title: str
    id: str
    status: str
    description: str
    references: list[str] = Field(default_factory=list)
    tags: list[str]
    logsource: SigmaLogsource
    detection: dict[str, Any]
    falsepositives: list[str]
    level: str
    provenance: dict[str, list[str]]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/schemas/sigma.py tests/unit/services/test_sigma_compiler.py
git commit -m "feat(compiler): add Sigma rule schema"
```

---

### Task 4: Sigma compiler for process creation ASTs

**Files:**
- Create: `src/de_forge/services/sigma_compiler.py`
- Modify: `tests/unit/services/test_sigma_compiler.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/services/test_sigma_compiler.py`:

```python
from de_forge.schemas.detection_ast import DetectionAst, FieldConditionNode, LogicGroupNode, LogicOperator
from de_forge.services.sigma_compiler import SigmaCompiler
from de_forge.services.telemetry_registry import TelemetryRegistry


def test_sigma_compiler_emits_process_creation_rule_from_ast() -> None:
    ast = DetectionAst(
        id="ast_1",
        detection_spec_id="spec_1",
        telemetry_source_id="sysmon_eid_1",
        attack_techniques=["T1059.001"],
        root=LogicGroupNode(
            id="group_1",
            operator=LogicOperator.ALL,
            children=[
                FieldConditionNode(
                    id="cond_1",
                    field="CommandLine",
                    operator="contains_any",
                    values=["-enc", "-EncodedCommand"],
                    evidence_ids=["evidence_1"],
                )
            ],
        ),
    )

    rule = SigmaCompiler(TelemetryRegistry.default()).compile(
        ast,
        title="Suspicious Encoded PowerShell Command",
        description="Detects encoded PowerShell command execution.",
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
    )

    assert rule.logsource.product == "windows"
    assert rule.logsource.category == "process_creation"
    assert rule.detection["selection_cond_1"] == {"CommandLine|contains": ["-enc", "-EncodedCommand"]}
    assert rule.detection["condition"] == "selection_cond_1"
    assert "attack.t1059.001" in rule.tags
    assert rule.provenance["selection_cond_1"] == ["evidence_1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py::test_sigma_compiler_emits_process_creation_rule_from_ast -v
```

Expected: FAIL with import error for `de_forge.services.sigma_compiler`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/sigma_compiler.py`:

```python
"""Compile Detection ASTs into Sigma rules."""

from de_forge.core.errors import ValidationGateError
from de_forge.core.hashing import snapshot_hash
from de_forge.schemas.detection_ast import DetectionAst, LogicOperator
from de_forge.schemas.sigma import SigmaLogsource, SigmaRule
from de_forge.services.telemetry_registry import TelemetryRegistry


class SigmaCompiler:
    """Compile validated Detection ASTs into typed Sigma rules."""

    def __init__(self, telemetry_registry: TelemetryRegistry) -> None:
        self.telemetry_registry = telemetry_registry

    def compile(
        self,
        ast: DetectionAst,
        title: str,
        description: str,
        falsepositives: list[str],
        level: str,
    ) -> SigmaRule:
        for condition in ast.root.children:
            if not self.telemetry_registry.field_exists(ast.telemetry_source_id, condition.field):
                raise ValidationGateError(f"field {condition.field} does not exist in {ast.telemetry_source_id}")

        detection: dict[str, object] = {}
        provenance: dict[str, list[str]] = {}
        selection_names: list[str] = []
        for condition in ast.root.children:
            selection_name = f"selection_{condition.id}"
            selection_names.append(selection_name)
            sigma_operator = self._sigma_operator(condition.operator)
            detection[selection_name] = {f"{condition.field}|{sigma_operator}": condition.values}
            provenance[selection_name] = condition.evidence_ids

        if ast.root.operator == LogicOperator.ALL:
            condition_expr = " and ".join(selection_names)
        elif ast.root.operator == LogicOperator.ANY:
            condition_expr = " or ".join(selection_names)
        else:
            condition_expr = f"not ({' or '.join(selection_names)})"
        detection["condition"] = condition_expr

        return SigmaRule(
            id=f"sigma_{snapshot_hash(ast.model_dump())[:16]}",
            title=title,
            status="experimental",
            description=description,
            references=[],
            tags=[f"attack.{technique.lower()}" for technique in ast.attack_techniques],
            logsource=self._logsource_for(ast.telemetry_source_id),
            detection=detection,
            falsepositives=falsepositives,
            level=level,
            provenance=provenance,
        )

    def _sigma_operator(self, operator: str) -> str:
        if operator in {"contains", "contains_any"}:
            return "contains"
        if operator == "equals":
            return "equals"
        raise ValidationGateError(f"unsupported AST operator {operator}")

    def _logsource_for(self, telemetry_source_id: str) -> SigmaLogsource:
        if telemetry_source_id in {"sysmon_eid_1", "windows_security_4688"}:
            return SigmaLogsource(product="windows", category="process_creation")
        if telemetry_source_id == "linux_auditd_execve":
            return SigmaLogsource(product="linux", category="process_creation")
        if telemetry_source_id == "zeek_conn":
            return SigmaLogsource(product="zeek", category="network_connection")
        raise ValidationGateError(f"unsupported telemetry source {telemetry_source_id}")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/sigma_compiler.py tests/unit/services/test_sigma_compiler.py
git commit -m "feat(compiler): compile detection ASTs to Sigma rules"
```

---

### Task 5: Sigma validator and YAML serialization

**Files:**
- Create: `src/de_forge/services/sigma_validator.py`
- Modify: `src/de_forge/services/sigma_compiler.py`
- Modify: `tests/unit/services/test_sigma_compiler.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/services/test_sigma_compiler.py`:

```python
import yaml

from de_forge.services.sigma_validator import SigmaValidator


def test_sigma_validator_rejects_missing_condition() -> None:
    rule = SigmaRule(
        title="Bad Rule",
        id="rule_bad",
        status="experimental",
        description="missing condition",
        references=[],
        tags=["attack.t1059.001"],
        logsource=SigmaLogsource(product="windows", category="process_creation"),
        detection={"selection_1": {"CommandLine|contains": ["-enc"]}},
        falsepositives=["admin usage"],
        level="medium",
        provenance={"selection_1": ["evidence_1"]},
    )

    assert SigmaValidator().validate(rule) is False


def test_sigma_compiler_serializes_rule_to_yaml() -> None:
    ast = DetectionAst(
        id="ast_1",
        detection_spec_id="spec_1",
        telemetry_source_id="sysmon_eid_1",
        attack_techniques=["T1059.001"],
        root=LogicGroupNode(
            id="group_1",
            operator=LogicOperator.ALL,
            children=[
                FieldConditionNode(
                    id="cond_1",
                    field="CommandLine",
                    operator="contains_any",
                    values=["-enc"],
                    evidence_ids=["evidence_1"],
                )
            ],
        ),
    )
    compiler = SigmaCompiler(TelemetryRegistry.default())
    rule = compiler.compile(
        ast,
        title="Suspicious Encoded PowerShell Command",
        description="Detects encoded PowerShell command execution.",
        falsepositives=["administrative encoded PowerShell usage"],
        level="medium",
    )

    serialized = compiler.to_yaml(rule)
    parsed = yaml.safe_load(serialized)

    assert parsed["title"] == "Suspicious Encoded PowerShell Command"
    assert parsed["detection"]["condition"] == "selection_cond_1"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py::test_sigma_validator_rejects_missing_condition tests/unit/services/test_sigma_compiler.py::test_sigma_compiler_serializes_rule_to_yaml -v
```

Expected: FAIL with import error for `de_forge.services.sigma_validator` or missing `to_yaml`.

- [ ] **Step 3: Write minimal implementation**

Create `src/de_forge/services/sigma_validator.py`:

```python
"""Deterministic Sigma structure validation."""

from de_forge.schemas.sigma import SigmaRule


class SigmaValidator:
    """Validate required Sigma structure before candidate ranking."""

    def validate(self, rule: SigmaRule) -> bool:
        if not rule.title.strip():
            return False
        if not rule.detection.get("condition"):
            return False
        selection_names = [key for key in rule.detection if key != "condition"]
        if not selection_names:
            return False
        condition = str(rule.detection["condition"])
        return all(selection_name in condition for selection_name in selection_names)
```

Modify `src/de_forge/services/sigma_compiler.py` to add import and method:

```python
import yaml
```

Add this method inside `SigmaCompiler`:

```python
    def to_yaml(self, rule: SigmaRule) -> str:
        """Serialize a Sigma rule to YAML, excluding internal provenance."""
        payload = rule.model_dump(exclude={"provenance"}, exclude_none=True)
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/unit/services/test_sigma_compiler.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/de_forge/services/sigma_validator.py src/de_forge/services/sigma_compiler.py tests/unit/services/test_sigma_compiler.py
git commit -m "feat(compiler): validate and serialize Sigma rules"
```

---

### Task 6: Full compiler verification

**Files:**
- Modify only if verification finds issues.

- [ ] **Step 1: Run compiler tests**

Run:

```bash
pytest tests/unit/services/test_detection_ast.py tests/unit/services/test_sigma_compiler.py -v
```

Expected: PASS.

- [ ] **Step 2: Run affected service tests**

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
git commit -m "test: verify compiler foundation"
```

If no fixes were required, do not create an empty commit.

---

## Self-review checklist

Spec coverage in this compiler plan:

- DetectionSpec -> Detection AST: Tasks 1-2.
- Detection AST -> Sigma object/YAML: Tasks 3-5.
- Reject unknown fields through telemetry registry: Task 4.
- Preserve provenance from condition to evidence ids: Tasks 3-4.
- Avoid free-form Sigma YAML as source of truth: Tasks 4-5.

Deferred to later plans:

- Rule portfolio generation.
- Static broad-rule validation beyond structure checks.
- Dynamic/adversarial/counterfactual evaluation.
- Oracle scoring.
- LLM agents.
- UI rendering of AST/provenance.
