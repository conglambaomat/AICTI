"""Pipeline orchestrator with hard-gated state transitions and full flow."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from de_forge.models import DetectionSpec as DetectionSpecModel
from de_forge.models import EvidenceSpan as EvidenceSpanModel
from de_forge.models import GeneratedRule as GeneratedRuleModel
from de_forge.models import PipelineRunRecord as PipelineRunRecordModel
from de_forge.models import ProofObligationRecord as ProofObligationRecordModel
from de_forge.models import Report as ReportModel
from de_forge.models import ValidationResult as ValidationResultModel
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

    def run_report_pipeline(self, *, report_id: str, run_id: str) -> PipelineRunRecordModel:
        report = self.db.get(ReportModel, report_id)
        if report is None:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="report_not_found",
                detection_spec_id=None,
                rule_id=None,
            )
            raise PipelineTransitionError("persisted Report required")

        evidence_rows = (
            self.db.execute(
                select(EvidenceSpanModel).where(EvidenceSpanModel.report_id == report_id)
            )
            .scalars()
            .all()
        )
        if not evidence_rows:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="evidence_required",
                detection_spec_id=None,
                rule_id=None,
            )
            raise PipelineTransitionError("evidence required before DetectionSpec generation")

        specs = (
            self.db.execute(
                select(DetectionSpecModel)
                .where(
                    DetectionSpecModel.report_id == report_id,
                    DetectionSpecModel.is_validated.is_(True),
                )
                .order_by(DetectionSpecModel.id)
            )
            .scalars()
            .all()
        )
        spec = specs[0] if specs else None
        if len(specs) > 1:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="detection_spec_ambiguous",
                detection_spec_id=spec.id,
                rule_id=None,
            )
            raise PipelineTransitionError("single validated DetectionSpec required")
        if spec is None or spec.abstain_code is not None or not spec.spec_payload:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="detection_spec_required",
                detection_spec_id=spec.id if spec is not None else None,
                rule_id=None,
            )
            raise PipelineTransitionError("validated DetectionSpec required")

        rules = (
            self.db.execute(
                select(GeneratedRuleModel)
                .where(GeneratedRuleModel.detection_spec_id == spec.id)
                .order_by(GeneratedRuleModel.id)
            )
            .scalars()
            .all()
        )
        populated_rules = [candidate for candidate in rules if candidate.rule_content]
        rule = populated_rules[0] if populated_rules else None
        if rule is None:
            generated = self.rule_generation.generate_sigma_rule(detection_spec_id=spec.id)
            rule = self.db.get(GeneratedRuleModel, generated.rule_id)
        if rule is None or not rule.rule_content:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="rule_generation_failed",
                detection_spec_id=spec.id,
                rule_id=None,
            )
            raise PipelineTransitionError("generated rule required before validation")

        validation = self.static_validator.validate_rule(rule.id)
        if not validation.is_valid:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="static_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("static validation gate failed")

        self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="failed",
            stage="evaluation_depth_required",
            detection_spec_id=spec.id,
            rule_id=rule.id,
        )
        raise PipelineTransitionError("evaluation-depth gate failed before review")

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

        self._require_evaluation_depth_passed(run_id=detection_spec_id, rule_id=rule.id)
        self._require_proof_obligations_proven(run_id=detection_spec_id, rule_id=rule.id)

        return PipelineState.AWAITING_REVIEW

    def _remember_pipeline_run(
        self,
        *,
        run_id: str,
        report_id: str,
        status: str,
        stage: str,
        detection_spec_id: str | None,
        rule_id: str | None,
    ) -> PipelineRunRecordModel:
        record = self.db.execute(
            select(PipelineRunRecordModel).where(PipelineRunRecordModel.run_id == run_id)
        ).scalar_one_or_none()
        if record is None:
            record = PipelineRunRecordModel(
                id=str(uuid4()),
                run_id=run_id,
                report_id=report_id,
                status=status,
                stage=stage,
                detection_spec_id=detection_spec_id,
                rule_id=rule_id,
                created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            )
            self.db.add(record)
        else:
            record.report_id = report_id
            record.status = status
            record.stage = stage
            record.detection_spec_id = detection_spec_id
            record.rule_id = rule_id
        self.db.commit()
        return record

    def _require_evaluation_depth_passed(self, *, run_id: str, rule_id: str) -> None:
        rows = (
            self.db.execute(
                select(ValidationResultModel).where(
                    ValidationResultModel.run_id == run_id,
                    ValidationResultModel.rule_id == rule_id,
                )
            )
            .scalars()
            .all()
        )
        if len(rows) < 4:
            raise PipelineTransitionError(
                "evaluation-depth gate failed: missing persisted outcomes"
            )

        if any(row.status.lower() != "passed" for row in rows):
            raise PipelineTransitionError("evaluation-depth gate failed before review")

    def _require_proof_obligations_proven(self, *, run_id: str, rule_id: str) -> None:
        rows = (
            self.db.execute(
                select(ProofObligationRecordModel).where(
                    ProofObligationRecordModel.run_id == run_id,
                    ProofObligationRecordModel.rule_candidate_id == rule_id,
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            raise PipelineTransitionError("proof obligation gate failed: no persisted obligations")

        disallowed = {"failed", "unknown", "not_applicable"}
        unresolved = [row for row in rows if row.status.lower() in disallowed]
        if unresolved:
            raise PipelineTransitionError("proof obligation gate failed before review")

        if any(row.status.lower() != "proven" for row in rows):
            raise PipelineTransitionError("proof obligation gate failed before review")

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
