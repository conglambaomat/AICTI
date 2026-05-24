# Ground-Truth Fixtures

## Purpose
Contains report-level ground-truth annotations for benchmark and regression evaluation.

## Structure
- `reports/simple/`
- `reports/medium/`
- `reports/hard/`

Each report has:
- `report_NNN.txt` or `report_NNN.pdf`
- `report_NNN_gt.json` conforming to `docs/benchmark/ground-truth-schema.json`

## Validation
Use schema validation against `docs/benchmark/ground-truth-schema.json` before benchmark runs.

## Usage in Benchmarks
The benchmark harness loads each `*_gt.json` and compares:
- evidence recall
- ATT&CK precision
- decision correctness (behavior_rule vs abstain)
- rule quality metrics
