# Agentic Upgrade Precedence Rules

Date: 2026-05-20
Scope: Conflict resolution between MVP baseline and agentic deep-analysis upgrade

## 1. Purpose
Define precedence rules when MVP baseline behavior conflicts with agentic upgrade requirements.

## 2. Core Principle
**Agentic upgrade MUST NOT break MVP contract guarantees.**

MVP contract guarantees (immutable):
- DetectionSpec-first invariant
- Hard gates (validated spec, abstain blocked, static validation pass)
- Bounded refinement loops (max 3 static, max 2 dynamic)
- Abstain policy (6 codes)
- Human review gate before export

## 3. Precedence Hierarchy

### Tier 1: MVP Contract (Highest Priority)
**Never override:**
- DetectionSpec schema structure
- Hard gate enforcement logic
- Abstain code semantics
- Human review requirement
- Loop limit enforcement

**If agentic upgrade conflicts:** Upgrade MUST adapt to preserve contract.

### Tier 2: Agentic Enhancement (Medium Priority)
**May extend but not replace:**
- Evidence extraction depth (MVP: regex-based → Agentic: LLM-based)
- ATT&CK mapping coverage (MVP: keyword match → Agentic: semantic reasoning)
- Retrieval strategy (MVP: none → Agentic: hybrid RAG)
- Validation granularity (MVP: basic → Agentic: fine-grained)

**If enhancement conflicts with Tier 1:** Tier 1 wins.

### Tier 3: Implementation Detail (Lowest Priority)
**May replace freely:**
- Internal data structures (as long as schema contract preserved)
- Caching strategy
- Logging format
- Performance optimization

## 4. Upgrade Compatibility Checklist

Before merging agentic upgrade, verify:
- [ ] DetectionSpec schema unchanged or backward-compatible
- [ ] Hard gates still enforced
- [ ] Loop limits respected
- [ ] Abstain codes semantically consistent
- [ ] Human review gate preserved
- [ ] MVP test suite passes (no regressions)
- [ ] Agentic tests added (no replacement of MVP tests)

## 5. Enforcement

Automated checks in CI:
- Run MVP test suite (must pass).
- Schema validation (must match contract).
- Loop limit enforcement test (must respect bounds).
- Abstain code coverage (must use only defined codes).

Manual review gate:
- Reviewer verifies precedence rules followed.
- Reviewer confirms no silent contract changes.
