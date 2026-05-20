"""Core constants for DE-Forge."""

IDEMPOTENCY_KEY_PREFIX = "idem_"

from typing import Mapping

PROFILE_THRESHOLDS: Mapping[str, Mapping[str, float | int]] = {
    "strict": {
        "static_validity_rate_min": 0.99,
        "dynamic_precision_min": 0.92,
        "dynamic_recall_min": 0.70,
        "dynamic_f1_min": 0.80,
        "overbroad_rule_rate_max": 0.03,
        "claim_supported_rate_min": 0.98,
        "citation_mismatch_rate_max": 0.01,
        "provenance_completeness_rate_min": 0.99,
        "tokens_per_report_p95_max": 120000,
        "seconds_per_report_p95_max": 120,
        "cost_per_report_p95_usd_max": 3.0,
    },
    "balanced": {
        "static_validity_rate_min": 0.98,
        "dynamic_precision_min": 0.85,
        "dynamic_recall_min": 0.80,
        "dynamic_f1_min": 0.82,
        "overbroad_rule_rate_max": 0.06,
        "claim_supported_rate_min": 0.95,
        "citation_mismatch_rate_max": 0.03,
        "provenance_completeness_rate_min": 0.97,
        "tokens_per_report_p95_max": 90000,
        "seconds_per_report_p95_max": 90,
        "cost_per_report_p95_usd_max": 2.0,
    },
    "exploratory": {
        "static_validity_rate_min": 0.95,
        "dynamic_precision_min": 0.75,
        "dynamic_recall_min": 0.88,
        "dynamic_f1_min": 0.80,
        "overbroad_rule_rate_max": 0.10,
        "claim_supported_rate_min": 0.90,
        "citation_mismatch_rate_max": 0.05,
        "provenance_completeness_rate_min": 0.93,
        "tokens_per_report_p95_max": 70000,
        "seconds_per_report_p95_max": 60,
        "cost_per_report_p95_usd_max": 1.2,
    },
}
