from __future__ import annotations

from collections.abc import Iterable, Mapping


class ProofCoverageError(ValueError):
    pass


_REQUIRED_CLAIMS = {
    "detects_report_behavior",
    "not_overbroad",
    "telemetry_fields_exist",
    "positive_tests_pass",
    "benign_baseline_not_matched",
    "citation_faithful",
    "oracle_expectations_satisfied",
    "regression_safe",
}

_NA_ALLOWED = {
    "positive_tests_pass",
    "benign_baseline_not_matched",
    "oracle_expectations_satisfied",
    "regression_safe",
}


class ProofCoverageService:
    def required_claim_types(self) -> set[str]:
        return set(_REQUIRED_CLAIMS)

    def assert_coverage_satisfied(
        self,
        *,
        run_id: str,
        rule_id: str,
        proof_rows: Iterable[Mapping[str, object]],
    ) -> None:
        current: dict[str, Mapping[str, object]] = {}
        for row in proof_rows:
            if row.get("run_id") != run_id or row.get("rule_candidate_id") != rule_id:
                continue
            claim_type = str(row.get("claim_type"))
            if claim_type in current:
                raise ProofCoverageError(f"duplicate current proof obligation: {claim_type}")
            current[claim_type] = row

        missing = sorted(_REQUIRED_CLAIMS - set(current))
        if missing:
            raise ProofCoverageError("missing required proof obligations: " + ", ".join(missing))

        for claim_type in sorted(_REQUIRED_CLAIMS):
            row = current[claim_type]
            status = str(row.get("status"))
            justification = str(row.get("justification") or "")
            if status == "proven":
                continue
            if status == "not_applicable" and claim_type in _NA_ALLOWED and justification:
                continue
            raise ProofCoverageError(f"proof obligation {claim_type} is {status}")
