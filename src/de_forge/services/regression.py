from __future__ import annotations

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.regression import RegressionTest
from de_forge.schemas.sigma import SigmaRule


class RegressionService:
    def __init__(self, regression_tests: list[RegressionTest]) -> None:
        self.regression_tests = regression_tests

    def assert_candidate_safe(self, candidate_patterns: list[str], rule: SigmaRule) -> bool:
        del rule
        for regression in self.regression_tests:
            if (
                regression.regression_type == "do_not_repeat"
                and regression.pattern in candidate_patterns
            ):
                raise ValidationGateError(
                    f"candidate repeats rejected pattern {regression.pattern}"
                )
        return True
