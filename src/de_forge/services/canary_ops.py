from __future__ import annotations

from typing import Any


class CanaryOpsService:
    def evaluate_canary(
        self,
        kpi_result: dict[str, Any],
        baseline_delta_pass: bool,
        profile: str,
    ) -> dict[str, Any]:
        for key in ("pass", "profile", "failures", "summary"):
            if key not in kpi_result:
                raise ValueError(f"kpi_result missing required key: {key}")

        if baseline_delta_pass is False:
            return {
                "action": "rollback",
                "rollback_required": True,
                "reason_code": "BASELINE_DELTA_FAIL",
                "profile": profile,
                "details": {
                    "kpi_pass": bool(kpi_result["pass"]),
                    "baseline_delta_pass": baseline_delta_pass,
                    "failures": list(kpi_result.get("failures", [])),
                },
            }

        if bool(kpi_result["pass"]) is False:
            return {
                "action": "rollback",
                "rollback_required": True,
                "reason_code": "KPI_GATE_FAIL",
                "profile": profile,
                "details": {
                    "kpi_pass": bool(kpi_result["pass"]),
                    "baseline_delta_pass": baseline_delta_pass,
                    "failures": list(kpi_result.get("failures", [])),
                },
            }

        return {
            "action": "promote",
            "rollback_required": False,
            "reason_code": "CANARY_PASS",
            "profile": profile,
            "details": {
                "kpi_pass": bool(kpi_result["pass"]),
                "baseline_delta_pass": baseline_delta_pass,
                "failures": [],
            },
        }
