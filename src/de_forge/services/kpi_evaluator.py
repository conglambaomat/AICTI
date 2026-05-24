from __future__ import annotations

from typing import Any


class KPIEvaluator:
    def evaluate_kpis(
        self,
        metrics: dict[str, dict[str, float]],
        thresholds: dict[str, dict[str, float]],
        profile: str,
    ) -> dict[str, Any]:
        failures: list[dict[str, Any]] = []

        for category, threshold_values in thresholds.items():
            category_metrics = metrics.get(category)
            if category_metrics is None:
                raise ValueError(f"Missing required KPI category: {category}")

            for metric_name, threshold_value in threshold_values.items():
                actual_value = category_metrics.get(metric_name)
                if actual_value is None:
                    raise ValueError(f"Missing required metric: {category}.{metric_name}")

                is_upper_bound = metric_name.startswith("max_") or (
                    category == "abstain_quality" and metric_name == "coverage"
                )
                if is_upper_bound:
                    if actual_value > threshold_value:
                        failures.append(
                            {
                                "category": category,
                                "metric": metric_name,
                                "actual": actual_value,
                                "required": threshold_value,
                                "operator": "<=",
                            }
                        )
                elif actual_value < threshold_value:
                    failures.append(
                        {
                            "category": category,
                            "metric": metric_name,
                            "actual": actual_value,
                            "required": threshold_value,
                            "operator": ">=",
                        }
                    )

        passed = not failures
        summary = "All KPI thresholds satisfied" if passed else "KPI threshold violations detected"

        return {
            "pass": passed,
            "profile": profile,
            "failures": failures,
            "summary": summary,
        }
