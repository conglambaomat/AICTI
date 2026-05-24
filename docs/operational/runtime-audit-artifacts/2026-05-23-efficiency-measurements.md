# Efficiency Measurements (Single-User)

| Run | Scenario | Total latency (s) | Stage latency evidence | Retry/timeout events | PASS/FAIL |
|---|---|---:|---|---|---|
| 1 | positive flow | 2.626 | `1 passed in 1.33s` test marker | none observed | PASS |
| 2 | positive flow | 2.589 | `1 passed in 1.32s` test marker | none observed | PASS |
| 3 | positive flow | 2.470 | `1 passed in 1.26s` test marker | none observed | PASS |

## Summary
- min: 2.470s
- median: 2.589s
- max: 2.626s
- variance note: low spread (0.156s) across repeated runs under single-user same-input conditions.
- efficiency verdict: PASS (single-user latency stable and low for measured synthetic active path).

## Limitation
Efficiency result is measured on the currently active `/v1` runtime contract path, which path-truth evidence shows is synthetic/stub-oriented for key production gates.
