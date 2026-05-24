# Canary and Rollback Runbook (Agentic Deep-Analysis)

Date: 2026-05-20
Scope: Production-minded rollout for upgraded no-OCR agentic stack

## 1. Rollout Strategy
Use staged canary exposure:
- Stage A: 5% candidate reports
- Stage B: 10-20% candidate reports
- Stage C: 50% candidate reports
- Stage D: full profile deployment

Advance only if current stage meets KPI gates for rolling window.

## 2. Canary Eligibility
A report is canary-eligible when:
- input format is supported (TXT/PDF text),
- no unresolved pipeline integrity errors,
- profile thresholds are configured.

## 3. Real-time Monitoring
Track rolling windows for:
- dynamic precision/recall/f1
- overbroad rate
- citation mismatch rate
- abstain precision/coverage
- cost/report and p95 latency
- reviewer reject rate

## 4. Rollback Triggers (Hard)
Rollback immediately if any trigger fires:
1. FP spike over profile threshold for 2 consecutive windows.
2. Citation mismatch rate above profile threshold.
3. Reviewer reject spike above threshold.
4. Cost/report breach above budget for 3 consecutive windows.
5. p95 latency breach above threshold for 3 consecutive windows.

## 5. Rollback Procedure
1. Set pipeline mode to previous stable revision.
2. Block new upgraded runs.
3. Mark current run set with rollback event id.
4. Notify reviewer/ops channel with incident summary.
5. Open regression investigation ticket.

## 6. Incident Metrics and SLO
- MTTD target: <= 30 minutes (strict), <= 45 (balanced), <= 60 (exploratory)
- MTTR rollback target: <= 15 minutes (strict), <= 20 (balanced), <= 30 (exploratory)

## 7. Post-Rollback Checklist
- identify root cause category (prompt, retrieval, model, gate logic, data drift)
- attach failing examples and evidence trace
- patch and rerun evaluation protocol
- re-enter rollout from Stage A only

## 8. Governance
No threshold changes during active incident response.
Threshold changes require documented postmortem and reviewer approval.
