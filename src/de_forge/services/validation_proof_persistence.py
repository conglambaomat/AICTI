"""Persistence services for validation and proof artifacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import GeneratedRule, ValidationResult
from de_forge.services.static_validation import ValidationReport


class ValidationProofPersistenceService:
    """Persist deterministic validation and proof results."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def record_static_validation(
        self, *, run_id: str, rule_id: str, report: ValidationReport
    ) -> str:
        rule = self.db.execute(
            select(GeneratedRule).where(GeneratedRule.id == rule_id)
        ).scalar_one_or_none()
        if rule is None:
            raise ValueError(f"rule_id {rule_id} not found")

        created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        result_id = str(uuid4())
        validation_result = ValidationResult(
            id=result_id,
            rule_id=rule_id,
            run_id=run_id,
            status="passed" if report.is_valid else "failed",
            details_json=json.dumps(
                {"validation_type": "static", "issues": report.issues}, sort_keys=True
            ),
            created_at=created_at,
        )
        self.db.add(validation_result)
        self.db.commit()
        return result_id
