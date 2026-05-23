# SUPERSEDED OUTLINE — DO NOT IMPLEMENT

This outline has been replaced by the full executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-compiler-plan.md`

Do not use this outline for implementation. It is preserved only as historical planning context.

---

# DE-Forge SOTA Core v2 Compiler Plan Outline

> **For agentic workers:** REQUIRED SUB-SKILL: Use the full executable compiler plan instead of this outline.

**Goal:** Implement Detection AST, Sigma AST, and deterministic Sigma compiler after the foundation plan passes.

**Architecture:** DetectionSpec is converted into Detection Logic AST, then Sigma AST, then Sigma YAML. LLM agents may propose intent later, but final YAML should be compiler-produced whenever possible.

**Tech Stack:** Python 3.11+, Pydantic v2, PyYAML, pytest, ruff, mypy.

---

## Prerequisites

- Foundation plan complete.
- DetectionSpec verifier exists.
- Telemetry registry exists.
- Proof obligation service exists.

## Target files

- `src/de_forge/schemas/detection_ast.py`
- `src/de_forge/schemas/sigma.py`
- `src/de_forge/services/detection_ast_service.py`
- `src/de_forge/services/sigma_compiler.py`
- `src/de_forge/services/sigma_validator.py`
- `tests/unit/services/test_detection_ast.py`
- `tests/unit/services/test_sigma_compiler.py`

## Required capabilities

1. Define AST nodes:
   - field condition,
   - any/all condition group,
   - not condition,
   - selection,
   - filter.
2. Convert verified DetectionSpec logic requirements into AST.
3. Compile AST into Sigma YAML object.
4. Validate field/logsource compatibility using telemetry registry.
5. Reject unsupported fields before YAML emission.
6. Preserve provenance from AST nodes to evidence ids and proof obligations.

## Golden test

Input:

- DetectionSpec for encoded PowerShell execution.
- Telemetry source `sysmon_eid_1`.
- Field `CommandLine` with values `-enc`, `-EncodedCommand`.

Expected:

- Sigma rule with process_creation logsource.
- Detection selection on CommandLine.
- Condition references selection.
- Tags include T1059.001.
- Compiler provenance links condition to evidence id.

## Exit criteria

- Sigma candidate is generated deterministically from AST.
- Unknown fields are rejected.
- Invalid condition trees are rejected.
- Compiler output can be parsed as YAML.
- Unit tests pass.
