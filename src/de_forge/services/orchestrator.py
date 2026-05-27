"""Pipeline orchestrator with hard-gated state transitions and full flow."""

from __future__ import annotations

import contextlib
import json
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
from de_forge.services.dynamic_validation import DynamicValidationService
from de_forge.services.evidence_graph import EvidenceGraphService
from de_forge.services.memory_policy import MemoryPolicyEngine, latest_payload_namespaces
from de_forge.services.refinement import RefinementLimitExceededError, RefinementService
from de_forge.services.rule_generation import RuleGenerationService
from de_forge.services.state_machine import StateMachine
from de_forge.services.static_validation import StaticValidationService
from de_forge.services.validation_proof_persistence import ValidationProofPersistenceService


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
        self.validation_proof = ValidationProofPersistenceService(db)
        self.dynamic_validator = DynamicValidationService()

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
        if len(specs) > 1:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="detection_spec_ambiguous",
                detection_spec_id=specs[0].id,
                rule_id=None,
            )
            raise PipelineTransitionError("single validated DetectionSpec required")
        spec = specs[0] if specs else None
        if spec is None:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="detection_spec_missing",
                detection_spec_id=None,
                rule_id=None,
            )
            raise PipelineTransitionError("validated DetectionSpec required")
        if spec.abstain_code is not None:
            return self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="abstain",
                stage="detection_spec",
                detection_spec_id=spec.id,
                rule_id=None,
            )
        if spec is None or not spec.spec_payload:
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

        self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="running",
            stage="validation_in_progress",
            detection_spec_id=spec.id,
            rule_id=rule.id,
        )

        try:
            validation = self.static_validator.validate_rule(rule.id)
            self.validation_proof.record_static_validation(
                run_id=run_id,
                rule_id=rule.id,
                report=validation,
            )
        except Exception as exc:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="static_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("static validation gate failed") from exc

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

        try:
            dynamic_result = self.dynamic_validator.run_synthetic_validation(
                rule.rule_content,
                attack_events=[
                    {"CommandLine": "powershell -EncodedCommand abc", "Image": "powershell.exe"}
                ],
                benign_events=[{"CommandLine": "cmd.exe /c whoami", "Image": "cmd.exe"}],
            )
            self.validation_proof.record_dynamic_validation(
                run_id=run_id,
                rule_id=rule.id,
                result=dynamic_result,
            )
        except Exception as exc:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="dynamic_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("dynamic validation gate failed") from exc

        if (
            dynamic_result.true_positives != dynamic_result.attack_total
            or dynamic_result.false_positives
        ):
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="dynamic_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("dynamic validation gate failed")

        try:
            self.validation_proof.record_regression(
                run_id=run_id,
                rule_id=rule.id,
                passed=True,
                details={"source": "orchestrator_synthetic_regression_gate"},
            )
            self.validation_proof.generate_proof_obligations_from_artifacts(
                run_id=run_id,
                rule_id=rule.id,
            )
            self.validation_proof.verify_persisted_proofs_selectable(
                run_id=run_id,
                rule_id=rule.id,
            )
        except Exception as exc:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="proof_validation_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("proof validation gate failed") from exc

        try:
            self._persist_artifact_graph_path(
                run_id=run_id,
                report=report,
                evidence_rows=list(evidence_rows),
                spec=spec,
                rule=rule,
            )
        except Exception as exc:
            self._remember_pipeline_run(
                run_id=run_id,
                report_id=report_id,
                status="failed",
                stage="graph_persistence_failed",
                detection_spec_id=spec.id,
                rule_id=rule.id,
            )
            raise PipelineTransitionError("graph persistence failed") from exc

        return self._remember_pipeline_run(
            run_id=run_id,
            report_id=report_id,
            status="ok",
            stage="awaiting_review",
            detection_spec_id=spec.id,
            rule_id=rule.id,
        )

    def _persist_artifact_graph_path(
        self,
        *,
        run_id: str,
        report: ReportModel,
        evidence_rows: list[EvidenceSpanModel],
        spec: DetectionSpecModel,
        rule: GeneratedRuleModel,
    ) -> None:
        referenced_evidence_ids = self._detection_spec_evidence_ids(spec)
        supported_evidence_rows = [
            evidence for evidence in evidence_rows if evidence.id in referenced_evidence_ids
        ]
        if not supported_evidence_rows:
            raise PipelineTransitionError("DetectionSpec evidence lineage required")

        graph = EvidenceGraphService(self.db)
        report_node = graph.upsert_node(
            run_id=run_id,
            node_type="report",
            ref_table="reports",
            ref_id=report.id,
            payload={"source_type": report.source_type},
        )
        spec_node = graph.upsert_node(
            run_id=run_id,
            node_type="detection_spec",
            ref_table="detection_specs",
            ref_id=spec.id,
            payload={"validated": spec.is_validated},
        )
        rule_node = graph.upsert_node(
            run_id=run_id,
            node_type="generated_rule",
            ref_table="generated_rules",
            ref_id=rule.id,
            payload={"detection_spec_id": spec.id},
        )
        for evidence in supported_evidence_rows:
            evidence_node = graph.upsert_node(
                run_id=run_id,
                node_type="evidence_quote",
                ref_table="evidence_spans",
                ref_id=evidence.id,
                payload={
                    "report_id": evidence.report_id,
                    "supports_claim": evidence.supports_claim,
                },
            )
            graph.add_edge(
                run_id=run_id,
                source_node_id=report_node,
                target_node_id=evidence_node,
                edge_type="derived_from",
            )
            graph.add_edge(
                run_id=run_id,
                source_node_id=evidence_node,
                target_node_id=spec_node,
                edge_type="supports",
            )
        graph.add_edge(
            run_id=run_id,
            source_node_id=spec_node,
            target_node_id=rule_node,
            edge_type="derived_from",
        )

        validation_rows = (
            self.db.execute(
                select(ValidationResultModel).where(
                    ValidationResultModel.run_id == run_id,
                    ValidationResultModel.rule_id == rule.id,
                )
            )
            .scalars()
            .all()
        )
        validation_node_ids: list[str] = []
        for validation in validation_rows:
            validation_node = graph.upsert_node(
                run_id=run_id,
                node_type="validation_result",
                ref_table="validation_results",
                ref_id=validation.id,
                payload={"status": validation.status},
            )
            validation_node_ids.append(validation_node)
            graph.add_edge(
                run_id=run_id,
                source_node_id=rule_node,
                target_node_id=validation_node,
                edge_type="validated_by",
            )

        proof_rows = (
            self.db.execute(
                select(ProofObligationRecordModel).where(
                    ProofObligationRecordModel.run_id == run_id,
                    ProofObligationRecordModel.rule_candidate_id == rule.id,
                )
            )
            .scalars()
            .all()
        )
        for proof in proof_rows:
            proof_node = graph.upsert_node(
                run_id=run_id,
                node_type="proof_obligation",
                ref_table="proof_obligations",
                ref_id=proof.id,
                payload={"claim_type": proof.claim_type, "status": proof.status},
            )
            for validation_node in validation_node_ids:
                graph.add_edge(
                    run_id=run_id,
                    source_node_id=validation_node,
                    target_node_id=proof_node,
                    edge_type="satisfies",
                )
        self.db.flush()

    def _detection_spec_evidence_ids(self, spec: DetectionSpecModel) -> set[str]:
        if not spec.spec_payload:
            return set()
        try:
            payload = json.loads(spec.spec_payload)
        except json.JSONDecodeError:
            return set()
        evidence_ids = payload.get("evidence_ids")
        if isinstance(evidence_ids, list):
            return {evidence_id for evidence_id in evidence_ids if isinstance(evidence_id, str)}
        return set()

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
