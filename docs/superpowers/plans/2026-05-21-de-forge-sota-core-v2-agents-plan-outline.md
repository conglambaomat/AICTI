# SUPERSEDED OUTLINE — DO NOT IMPLEMENT

This outline has been replaced by the full executable plan:

- `docs/superpowers/plans/2026-05-21-de-forge-sota-core-v2-agents-plan.md`

Do not use this outline for implementation. It is preserved only as historical planning context.

---

# DE-Forge SOTA Core v2 Controlled Agents Plan Outline

> **For agentic workers:** REQUIRED SUB-SKILL: Use the full executable controlled agents plan instead of this outline.

**Goal:** Add controlled LLM-backed agents only after deterministic validators, graph, DetectionSpec, proof obligations, and compiler foundations exist.

**Architecture:** Every agent receives strict input schemas and returns strict JSON output. Outputs are never trusted directly; they pass schema validation, citation verification when applicable, registry validation, persistence, and gate checks before downstream use.

**Tech Stack:** Python 3.11+, OpenAI-compatible API client, Pydantic v2, httpx, pytest, ruff, mypy.

---

## Prerequisites

- Foundation plan complete.
- Compiler plan complete.
- Static validation plan complete.

## Target files

- `src/de_forge/services/llm_client.py`
- `src/de_forge/services/prompt_registry.py`
- `src/de_forge/agents/base.py`
- `src/de_forge/agents/evidence_agent.py`
- `src/de_forge/agents/entity_agent.py`
- `src/de_forge/agents/behavior_agent.py`
- `src/de_forge/agents/attack_mapping_agent.py`
- `src/de_forge/agents/detection_strategy_agent.py`
- `src/de_forge/agents/telemetry_agent.py`
- `src/de_forge/agents/detection_spec_agent.py`
- `src/de_forge/agents/detection_logic_agent.py`
- `src/de_forge/agents/critic_agent.py`
- `src/de_forge/agents/refinement_agent.py`
- `src/de_forge/agents/ranking_agent.py`
- `tests/unit/agents/test_agent_contracts.py`
- `tests/integration/agents/test_agent_audit.py`

## Required capabilities

1. Unified LLM client:
   - provider: OpenAI-compatible,
   - base URL from settings,
   - model from settings,
   - no fallback model logic,
   - timeout and retry policy,
   - token/cost/latency metadata capture.
2. Prompt registry:
   - versioned prompts,
   - prompt id stored in agent runs.
3. Agent envelope:
   - run id,
   - agent name,
   - input artifact ids,
   - output,
   - citations,
   - abstain flag,
   - metadata.
4. Agent audit persistence.
5. Schema rejection for invalid outputs.
6. Citation-bearing agent outputs must pass exact citation verification.

## Exit criteria

- Invalid JSON output is rejected.
- Invalid schema output is rejected.
- Citation mismatch is hard failure.
- Agent run audit is persisted with hashes and metadata.
- Agents cannot bypass graph/spec/proof validators.
