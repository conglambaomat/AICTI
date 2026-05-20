# ULTRA-AUTONOMOUS EXECUTION DIRECTIVE — DE-FORGE v2 (OPTIMIZED)

You are executing DE-Forge in maximum autonomous mode with Superpowers.
Primary objective: deliver a correct, stable, production-minded MVP end-to-end before benchmark optimization.

## 0) AUTHORITY & PRECEDENCE (STRICT)
Follow this precedence order for all decisions:
1. `E:/Khoaluanfinal/ai-threat-detection/CLAUDE.md`
2. `E:/Khoaluanfinal/CLAUDE.md`
3. Architecture/spec/implementation docs under `docs/`
4. This directive

If conflicts exist, obey higher-priority source and record a short "conflict resolution note" in the current spec/plan artifact.

## 1) AUTONOMY CONTRACT
Run continuously without asking "should I continue?".
Stop only when:
1) true technical blocker you cannot resolve,
2) requirement contradiction not resolvable from docs,
3) irreversible/destructive action outside local safe scope.

When stopped, output exactly:
- **Blocker**
- **Root cause**
- **Best next action**

## 2) MANDATORY WORKFLOW (SUPERPOWERS, NO SKIPS)
Execute in this exact order:
1. **brainstorming**
2. **writing-plans**
3. **subagent-driven-development**
4. **finishing-a-development-branch**

Enforcement rules:
- No implementation before approved design spec.
- One implementer subagent per task.
- Per task: implementer → spec review → code quality review.
- Fix and re-review until pass.
- TDD required per task: RED → GREEN → REFACTOR.

## 3) CORE INVARIANTS (NON-NEGOTIABLE)
- DetectionSpec-first invariant is mandatory (never raw report → rule direct).
- Retry/state semantics must follow: `docs/architecture/08-canonical-retry-state.md`.
- Respect bounded refinement loops from project CLAUDE.md.
- No Docker for MVP runtime.
- No fallback model/feature unless explicitly requested.

## 4) EXECUTION STRATEGY
### Phase A — Preflight (must finish first)
- Verify environment/config/entrypoints/commands.
- Normalize dev verification commands to real repo state.
- Create/update Superpowers artifacts in:
  - `docs/superpowers/specs/`
  - `docs/superpowers/plans/`

### Phase B — MVP Build
Implement only in-scope MVP pipeline:
1) Ingestion + deterministic chunking
2) Evidence extraction
3) ATT&CK mapping + abstain
4) Telemetry grounding
5) DetectionSpec builder + strict validation
6) Sigma-first generation
7) Static validation gates
8) Minimal dynamic validation
9) Bounded refinement loop
10) Human review gate + export policy

### Phase C — Reliability & Observability
- Structured logs, core metrics, error taxonomy alignment.
- Idempotency/transactions/persistence lineage contracts enforced.

### Phase D — Quality Gates
Must pass before done:
- `pytest`
- `mypy src/`
- `ruff check src/`
- `ruff format --check src/`

## 5) SCOPE CONTROL
- Product robustness first, benchmark second.
- Keep MVP tightly scoped to defined Sysmon + ATT&CK targets.
- No out-of-scope features before core pipeline is fully runnable/testable.

## 6) DEFINITION OF DONE (STRICT)
Finish only if all are true:
1. End-to-end flow runs: report → DetectionSpec → validated artifact → human review gate.
2. DetectionSpec-first invariant always holds.
3. Retry/state complies with canonical 08.
4. Persistence/lineage/idempotency comply with contract docs.
5. Schemas/contracts pass against documented JSON schemas.
6. Test/lint/typecheck pass.
7. Final report delivered with:
   - requirement→implementation mapping,
   - file-level change summary,
   - verification evidence,
   - known limitations + prioritized next steps.

## 7) OUTPUT POLICY DURING EXECUTION
Do not send progress chatter.
Only send messages when:
- blocked (using 3-field blocker format), or
- full Definition of Done is satisfied (final report).

Begin now.
