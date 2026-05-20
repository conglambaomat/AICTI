# DE-Forge KPI Threshold Matrix (Agentic Deep-Analysis)

Date: 2026-05-20
Scope: No-OCR, TXT/PDF text-based reports

## Purpose
Define profile-specific hard thresholds that must be met for stage advancement and rollout decisions.

Profiles:
- strict (high-risk detections)
- balanced (default production)
- exploratory (analyst exploration)

## 1. Quality Metrics
| Metric | strict | balanced | exploratory |
|---|---:|---:|---:|
| static_validity_rate | >= 0.99 | >= 0.98 | >= 0.95 |
| dynamic_precision | >= 0.92 | >= 0.85 | >= 0.75 |
| dynamic_recall | >= 0.70 | >= 0.80 | >= 0.88 |
| dynamic_f1 | >= 0.80 | >= 0.82 | >= 0.80 |
| overbroad_rule_rate | <= 0.03 | <= 0.06 | <= 0.10 |

## 2. Abstain Quality Metrics
| Metric | strict | balanced | exploratory |
|---|---:|---:|---:|
| abstain_precision | >= 0.90 | >= 0.85 | >= 0.75 |
| abstain_coverage | 0.10-0.35 | 0.05-0.25 | 0.02-0.20 |
| abstain_abuse_guard | pass | pass | pass |

Abstain abuse guard rule:
- Fail if abstain_coverage increases by > 20% relative while abstain_precision drops by > 5% absolute over rolling evaluation window.

## 3. Retrieval Faithfulness Metrics
| Metric | strict | balanced | exploratory |
|---|---:|---:|---:|
| claim_supported_rate | >= 0.98 | >= 0.95 | >= 0.90 |
| citation_mismatch_rate | <= 0.01 | <= 0.03 | <= 0.05 |
| provenance_completeness_rate | >= 0.99 | >= 0.97 | >= 0.93 |

## 4. Cost and Latency Metrics
| Metric | strict | balanced | exploratory |
|---|---:|---:|---:|
| tokens_per_report (p95) | <= 120000 | <= 90000 | <= 70000 |
| seconds_per_report (p95) | <= 120 | <= 90 | <= 60 |
| cost_per_report (p95, USD) | <= 3.00 | <= 2.00 | <= 1.20 |
| p95_stage_latency_breach_count | 0 | <= 1 | <= 2 |

## 5. Operational Metrics
| Metric | strict | balanced | exploratory |
|---|---:|---:|---:|
| reviewer_acceptance_rate | >= 0.80 | >= 0.72 | >= 0.60 |
| mttd_regression_minutes | <= 30 | <= 45 | <= 60 |
| mttr_rollback_minutes | <= 15 | <= 20 | <= 30 |

## 6. Gate Policy
A run profile is PASS only if:
1. All profile metrics pass thresholds.
2. No hard-fail event occurs:
   - schema contract violation
   - citation mismatch hard fail
   - state transition violation
   - loop limit breach

## 7. Baseline Comparison Requirement
For each evaluation run:
- Report absolute metrics and delta against non-AI baseline.
- Required for promotion:
  - balanced: dynamic_f1 delta >= +0.05 and claim_supported_rate delta >= +0.05
  - strict: dynamic_precision delta >= +0.05 and overbroad_rate delta <= -0.02

## 8. Change Control
Threshold updates require:
1. documented rationale,
2. backtest report,
3. reviewer sign-off.
