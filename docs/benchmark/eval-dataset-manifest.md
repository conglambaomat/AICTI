# Evaluation Dataset Manifest

Date: 2026-05-20
Scope: Dataset composition, ground-truth format, baseline delta protocol for deep-analysis evaluation

## 1. Purpose
Define dataset structure and baseline-vs-upgrade evaluation protocol.

## 2. Dataset Composition
- Total reports: 50
- Simple: 20
- Medium: 20
- Hard: 10
- TXT/PDF only (no OCR pipeline in this phase)

## 3. Ground-Truth Location
`tests/fixtures/ground_truth/`

## 4. Baseline Results Location
`tests/fixtures/baseline/mvp_baseline_results.json`

## 5. Required Baseline Delta Gates
- Evidence recall: +5% vs MVP baseline
- ATT&CK precision: +5%
- Rule precision: +5%
- Rule recall: +5%
- Abstain precision/coverage: no regression
- Token p95: <= +20% vs baseline
- Latency p95: <= +20% vs baseline

## 6. Evaluation Command
`pytest tests/benchmark/test_baseline_delta.py -v`

## 7. Pass/Fail Rule
Pass only if all quality gates are met and cost/latency remain within budget.
