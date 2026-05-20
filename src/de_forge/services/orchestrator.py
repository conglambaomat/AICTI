"""Pipeline orchestrator with hard-gated state transitions and full flow."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.services.attack_mapping import AttackMappingService
from de_forge.services.canary_ops import CanaryOpsService
from de_forge.services.detection_spec import DetectionSpecService
from de_forge.services.kpi_evaluator import KPIEvaluator
from de_forge.services.refinement import RefinementController
from de_forge.services.rule_generation import RuleGenerationService
from de_forge.services.static_validation import StaticValidationService


class PipelineState(StrEnum):
    INGESTED = "ingested"
    SPEC_VALIDATED = "spec_validated"
    RULE_GENERATED = "rule_generated"
    STATIC_VALIDATED = "static_validated"
    AWAITING_REVIEW = "awaiting_review"


class PipelineTransitionError(ValueError):
    """Raised when a hard gate blocks pipeline transition."""


class PipelineOrchestrator:
    """Orchestrates deterministic, hard-gated stage transitions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.static_validator = StaticValidationService(db)

    def run_pipeline(self, detection_spec_id: str) -> PipelineState:
        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None or not spec.is_validated:
            raise PipelineTransitionError("validated DetectionSpec required")
        if spec.abstain_code is not None:
            raise PipelineTransitionError("abstain DetectionSpec cannot proceed to rule generation")

        rule = self.db.execute(
            select(GeneratedRuleModel).where(GeneratedRuleModel.detection_spec_id == detection_spec_id)
        ).scalar_one_or_none()
        if rule is None:
            raise PipelineTransitionError("generated rule required before validation")

        validation = self.static_validator.validate_rule(rule.id)
        if not validation.is_valid:
            raise PipelineTransitionError("static validation gate failed")

        return PipelineState.AWAITING_REVIEW


class OrchestratorService:
    def __init__(self) -> None:
        self.attack_mapping = AttackMappingService()
        self.detection_spec = DetectionSpecService()
        self.rule_generation = RuleGenerationService()
        self.refinement = RefinementController(max_iterations=3)
        self.kpi_evaluator = KPIEvaluator()
        self.canary_ops = CanaryOpsService()

    def run_pipeline(
        self,
        report_text: str,
        profile: str,
        telemetry_registry: dict[str, list[str]],
        baseline_delta_pass: bool,
        validation_issues: list[dict[str, Any]],
        iteration: int,
    ) -> dict[str, Any]:
        if not report_text or not report_text.strip():
            raise ValueError("report_text must not be empty")

        evidence_spans = self._extract_evidence_stub(report_text)

        if not evidence_spans:
            return {
                "abstain": True,
                "stage": "evidence",
                "reason": "No evidence extracted from report",
                "profile": profile,
            }

        attack_result = self.attack_mapping.map_attack(evidence_spans, profile)
        if attack_result.get("abstain") is True:
            return {
                "abstain": True,
                "stage": "attack_mapping",
                "reason": attack_result.get("abstain_reason", "ATT&CK mapping abstained"),
                "profile": profile,
            }

        detection_spec = self.detection_spec.build_detection_spec(
            evidence_spans=evidence_spans,
            attack_mappings=attack_result["mappings"],
            telemetry_registry=telemetry_registry,
            profile=profile,
        )

        if detection_spec.get("abstain") is True:
            return {
                "abstain": True,
                "stage": "detection_spec",
                "reason": detection_spec.get("abstain_reason", "DetectionSpec abstained"),
                "profile": profile,
            }

        rule_result = self.rule_generation.generate_rule(detection_spec, profile)
        if rule_result.get("abstain") is True:
            return {
                "abstain": True,
                "stage": "rule_generation",
                "reason": rule_result.get("abstain_reason", "Rule generation abstained"),
                "profile": profile,
            }

        sigma_rule = rule_result["sigma_rule"]

        if validation_issues:
            refinement_result = self.refinement.refine(
                current_rule=sigma_rule,
                validation_issues=validation_issues,
                detection_spec=detection_spec,
                iteration=iteration,
            )
            if refinement_result["should_abort"]:
                return {
                    "abstain": True,
                    "stage": "refinement",
                    "reason": refinement_result["abort_reason"],
                    "profile": profile,
                }
            sigma_rule = refinement_result["revised_sigma_rule"]

        mock_metrics = {
            "evidence_extraction": {"recall": 0.90, "precision": 0.85},
            "attack_mapping": {"accuracy": 0.92},
            "rule_quality": {"precision": 0.78, "recall": 0.73, "f1": 0.75},
            "abstain_quality": {"precision": 0.82, "coverage": 0.12},
            "cost_budget": {"max_cost_usd": 3.5},
            "latency_budget": {"max_latency_seconds": 95.0},
        }
        mock_thresholds = {
            "evidence_extraction": {"recall": 0.85, "precision": 0.80},
            "attack_mapping": {"accuracy": 0.90},
            "rule_quality": {"precision": 0.75, "recall": 0.70, "f1": 0.72},
            "abstain_quality": {"precision": 0.80, "coverage": 0.15},
            "cost_budget": {"max_cost_usd": 5.0},
            "latency_budget": {"max_latency_seconds": 120.0},
        }

        kpi_result = self.kpi_evaluator.evaluate_kpis(
            metrics=mock_metrics,
            thresholds=mock_thresholds,
            profile=profile,
        )

        canary_decision = self.canary_ops.evaluate_canary(
            kpi_result=kpi_result,
            baseline_delta_pass=baseline_delta_pass,
            profile=profile,
        )

        return {
            "abstain": False,
            "sigma_rule": sigma_rule,
            "detection_spec": detection_spec,
            "kpi": kpi_result,
            "canary": canary_decision,
            "profile": profile,
        }

    def _extract_evidence_stub(self, report_text: str) -> list[dict[str, Any]]:
        if "PowerShell" in report_text or "powershell" in report_text.lower():
            return [
                {
                    "evidence_id": "e1",
                    "behavior_label": "suspicious_scripting",
                    "quote": "PowerShell execution detected",
                }
            ]
        return []
