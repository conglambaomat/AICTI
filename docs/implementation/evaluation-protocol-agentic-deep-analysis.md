# Evaluation Protocol: Agentic Deep-Analysis Upgrade

Date: 2026-05-20
Scope: No-OCR text reports

## 1. Objective
Provide reproducible, profile-aware evaluation proving quality, faithfulness, abstain behavior, and efficiency gains versus non-AI baseline.

## 2. Dataset Composition
Include at minimum:
1. high-signal attack reports
2. ambiguous low-signal reports
3. noisy reports with irrelevant details
4. long-context reports
5. benign/false-positive challenge reports

Each sample must have ground truth bundles:
- evidence labels
- ATT&CK labels
- expected detection constraints
- synthetic attack/benign behavior expectations

## 3. Baseline Requirement
Run non-AI baseline pipeline on the same corpus.
Metrics must include absolute and delta vs baseline.

## 4. Evaluation Steps
1. Freeze prompt versions and model settings.
2. Run strict profile evaluation.
3. Run balanced profile evaluation.
4. Run exploratory profile evaluation.
5. Compute KPI matrix and pass/fail.
6. Compute baseline delta report.
7. Produce risk summary and promotion recommendation.

## 5. Reproducibility Rules
- deterministic chunking and retrieval ordering where configured
- fixed random seeds for any stochastic fallback
- persist run_id, trace_id, prompt_version, model_id, retrieval_set_hash

## 6. Hard Failure Conditions
Immediately fail evaluation if any of:
- schema contract parse failure rate > 0
- citation mismatch above profile threshold
- state-machine transition violation
- loop-bound violation

## 7. Required Reports
1. run summary by profile
2. quality metrics
3. abstain quality metrics
4. retrieval faithfulness metrics
5. cost/latency metrics
6. baseline delta analysis
7. failure case audit table

## 8. Promotion Rule
A candidate is promotable when:
- all profile gates pass for intended deployment profile,
- no hard-fail events,
- baseline delta conditions in KPI matrix are met,
- reviewer sign-off is recorded.
