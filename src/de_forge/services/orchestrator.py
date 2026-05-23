"""Pipeline orchestrator with hard-gated state transitions and full flow."""

from __future__ import annotations

import contextlib
from enum import StrEnum

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.schemas.run import RunMode, RunState, RunSummary
from de_forge.services.agent_audit import AgentAuditService
from de_forge.services.memory_policy import MemoryPolicyEngine, latest_payload_namespaces
from de_forge.services.refinement import RefinementLimitExceededError, RefinementService
from de_forge.services.rule_generation import RuleGenerationService
from de_forge.services.state_machine import StateMachine
from de_forge.services.static_validation import StaticValidationService


class Orchestrator:
    def __init__(self) -> None:
        self.state_machine = StateMachine()

    def run_golden_path(self, report_id: str, report_text: str, mode: RunMode) -> RunSummary:
        del report_text
        state = RunState.CREATED
        state = self.state_machine.transition(state, RunState.INGESTED)
        state = self.state_machine.transition(state, RunState.EVIDENCE_READY)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_READY)
        if mode == RunMode.CAUTIOUS:
            return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)
        state = self.state_machine.transition(state, RunState.DETECTION_SPEC_VERIFIED)
        state = self.state_machine.transition(state, RunState.RULE_CANDIDATES_READY)
        state = self.state_machine.transition(state, RunState.VALIDATED)
        state = self.state_machine.transition(state, RunState.AWAITING_REVIEW)
        return RunSummary(id=f"run_{report_id}", mode=mode, state=state, report_id=report_id)


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
        self.rule_generation = RuleGenerationService(db)
        self.agent_audit = AgentAuditService(db)
        self.refinement = RefinementService(db)
        self.memory_policy = MemoryPolicyEngine()

    def run_pipeline(self, detection_spec_id: str) -> PipelineState:
        spec = self.db.execute(
            select(DetectionSpecModel).where(DetectionSpecModel.id == detection_spec_id)
        ).scalar_one_or_none()

        if spec is None or not spec.is_validated:
            raise PipelineTransitionError("validated DetectionSpec required")
        if spec.abstain_code is not None:
            raise PipelineTransitionError("abstain DetectionSpec cannot proceed to rule generation")

        if not spec.spec_payload:
            raise PipelineTransitionError("DetectionSpec payload required")

        self._require_memory_contract(run_id=detection_spec_id, stage="rule_generation")

        rule = self.db.execute(
            select(GeneratedRuleModel).where(
                GeneratedRuleModel.detection_spec_id == detection_spec_id
            )
        ).scalar_one_or_none()
        if rule is None:
            generated = self.rule_generation.generate_sigma_rule(
                detection_spec_id=detection_spec_id
            )
            self.agent_audit.persist_agent_run(
                run_id=detection_spec_id,
                trace_id=detection_spec_id,
                agent_name="rule_generation",
                input_snapshot={"detection_spec_id": detection_spec_id},
                output_snapshot={"rule_id": generated.rule_id},
                status="success",
            )
            rule = self.db.get(GeneratedRuleModel, generated.rule_id)
            if rule is None:
                raise PipelineTransitionError("generated rule required before validation")

        self._require_memory_contract(run_id=detection_spec_id, stage="static_validation")

        validation = self.static_validator.validate_rule(rule.id)
        self.agent_audit.persist_agent_run(
            run_id=detection_spec_id,
            trace_id=detection_spec_id,
            agent_name="static_validation",
            input_snapshot={"rule_id": rule.id},
            output_snapshot={"is_valid": validation.is_valid, "issues": validation.issues},
            status="success" if validation.is_valid else "failed",
        )
        if not validation.is_valid:
            with contextlib.suppress(RefinementLimitExceededError):
                self.refinement.record_rule_refinement(rule.id)
            raise PipelineTransitionError("static validation gate failed")

        return PipelineState.AWAITING_REVIEW

    def _require_memory_contract(self, *, run_id: str, stage: str) -> None:
        rows = self.db.execute(
            text(
                """
                SELECT scope, value
                FROM memory_views
                WHERE scope LIKE :prefix AND key = 'latest'
                """
            ),
            {"prefix": f"{run_id}:%"},
        ).fetchall()
        available_namespaces = latest_payload_namespaces(
            [(str(row[0]), str(row[1])) for row in rows]
        )
        missing = self.memory_policy.stage_contract_missing(
            stage=stage,
            available_namespaces=available_namespaces,
        )
        if missing:
            raise PipelineTransitionError(
                f"memory contract missing for stage {stage}: {', '.join(missing)}"
            )
