from __future__ import annotations

from pydantic import BaseModel


class RegressionTest(BaseModel):
    id: str
    regression_type: str
    pattern: str
    source_rule_candidate_id: str
    reason: str
