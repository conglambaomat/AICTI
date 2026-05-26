"""Rule generation service for DetectionSpec-gated Sigma output and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.schemas.detection_spec import DetectionSpec
from de_forge.services.detection_ast_service import DetectionAstService
from de_forge.services.sigma_compiler import SigmaCompiler


class UnvalidatedDetectionSpecError(ValueError):
    """Raised when rule generation is attempted with unvalidated DetectionSpec."""


@dataclass(frozen=True)
class RuleGenerationResult:
    """Result payload for persisted generated rule."""

    rule_id: str
    detection_spec_id: str


class RuleGenerationService:
    """Service for Sigma rule generation with optional persistence."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def generate_rule(self, detection_spec: dict[str, Any], profile: str) -> dict[str, Any]:
        if detection_spec.get("abstain") is True:
            return {
                "sigma_rule": {},
                "abstain": True,
                "abstain_reason": str(
                    detection_spec.get("abstain_reason", "DetectionSpec abstained")
                ),
                "metadata": {"profile": profile},
            }

        spec = DetectionSpec.model_validate(detection_spec)
        ast = DetectionAstService().from_spec(spec)
        compiled = SigmaCompiler().compile(
            ast,
            title="DE-Forge Generated Suspicious Process Execution",
            description="Generated from validated DetectionSpec",
            falsepositives=[],
            level="high" if profile == "strict" else "medium",
        )

        return {
            "sigma_rule": compiled.model_dump(exclude={"provenance"}, exclude_none=True),
            "abstain": False,
            "metadata": {"profile": profile},
        }

    def generate_sigma_rule(self, detection_spec_id: str) -> RuleGenerationResult:
        if self.db is None:
            raise ValueError("Database session required for persistent rule generation")

        spec = self._get_validated_detection_spec(detection_spec_id=detection_spec_id)
        rule_id = str(uuid4())
        rule_content = self._materialize_sigma_from_spec(spec)

        try:
            self.db.add(
                GeneratedRuleModel(
                    id=rule_id,
                    detection_spec_id=spec.id,
                    rule_content=rule_content,
                    generation_source="compiler",
                    detection_ast_id=f"ast-{rule_id}",
                    compiled_sigma_id=f"sigma-{rule_id}",
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return RuleGenerationResult(rule_id=rule_id, detection_spec_id=spec.id)

    def _get_validated_detection_spec(self, detection_spec_id: str) -> DetectionSpecModel:
        if self.db is None:
            raise ValueError("Database session required")

        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None:
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )
        if spec.abstain_code is not None:
            raise UnvalidatedDetectionSpecError(f"DetectionSpec {detection_spec_id} is abstain")
        if not spec.is_validated:
            raise UnvalidatedDetectionSpecError(
                f"DetectionSpec {detection_spec_id} not found or not validated"
            )

        return spec

    def _materialize_sigma_from_spec(self, spec: DetectionSpecModel) -> str:
        if not spec.spec_payload:
            raise ValueError("DetectionSpec missing spec_payload for constrained rule generation")

        detection_spec = DetectionSpec.model_validate_json(spec.spec_payload)
        ast = DetectionAstService().from_spec(detection_spec)
        compiled = SigmaCompiler().compile(
            ast,
            title="DE-Forge Generated Suspicious Process Execution",
            description="Generated from validated DetectionSpec",
            falsepositives=[],
            level="medium",
        )
        return SigmaCompiler().to_yaml(compiled)
