# DE-Forge SOTA Core v2 Design

Date: 2026-05-21
Status: Approved for implementation planning
Architecture name: Proof-Carrying Evidence-Graph Controlled Multi-Agent Detection Engineering System

## 1. Goal

Build DE-Forge into a single-user, production-grade, multi-agent detection engineering system that converts English TXT/PDF threat reports into evidence-grounded Sigma detection artifacts with maximum practical accuracy, strong citation faithfulness, high automation, and human final review.

The system prioritizes:

1. Highest practical detection accuracy: reduce false positives and false negatives; generated rules must be suitable for real detection engineering review.
2. Strong evidence and citation faithfulness: every major claim, behavior, mapping, telemetry requirement, and rule condition must trace to report evidence or a verified registry.
3. High automation: the pipeline should run from report to final review automatically in auto mode, while cautious mode pauses at critical uncertainty points.
4. Full auditability: store reports, chunks, evidence, prompts, model inputs/outputs, DetectionSpecs, rule versions, validation results, proof obligations, review decisions, token/cost/latency, feedback, and regression history.

Benchmark/research proof, including CTI-REALM integration, is deferred until the core product-mode pipeline is stable, but the architecture must support it.

## 2. Non-goals

The current target does not include:

- Multi-user or multi-tenant enterprise features.
- Billing, organizations, role-based access control, or SaaS administration.
- Auto-deployment to production SIEM without human approval.
- OCR for scanned/image-only reports in the first implementation track.
- Direct raw-report-to-rule generation.
- Free-form unbounded agent debate.
- Multiple model/provider ensembles in the first implementation track.

## 3. Input and output scope

Initial input scope:

- English standard TXT/PDF threat reports from sources such as Mandiant, Microsoft, CISA, Unit42, CrowdStrike, and similar vendors.
- Text-based PDFs only; OCR is deferred.

Initial output scope:

- Sigma-first rule generation.
- Translation to KQL/SPL/Elastic EQL is deferred, but the Detection AST and compiler design must allow future translators.

Initial telemetry scope is multi-platform from the start:

- Windows Sysmon.
- Windows Security Event Log.
- Linux auditd.
- Zeek/network telemetry.

## 4. Core architecture

DE-Forge SOTA Core v2 uses this pipeline:

```text
English TXT/PDF Threat Report
  -> Deterministic Ingestion + Chunking
  -> Hybrid, Section-Aware, Graph-Aware Retrieval
  -> Evidence Graph Construction
  -> Controlled Multi-Agent Analysis
  -> ATT&CK Detection Strategy / Analytic / Data Component Mapping
  -> Formal DetectionSpec Generation + Verification
  -> Proof Obligation Generation
  -> Detection Logic AST
  -> Sigma Compiler
  -> Rule Portfolio
  -> Static Validation
  -> Dynamic + Adversarial Validation
  -> Oracle Evaluation when oracle data exists
  -> Counterfactual Rule Evaluation
  -> Proof Obligation Verification
  -> Multi-objective Candidate Ranking
  -> Human Review UI
  -> Feedback Learning
  -> Detection CI/CD Regression
```

The system must never generate production detection rules directly from raw report text. The mandatory path is:

```text
raw report -> evidence graph -> verified DetectionSpec -> detection AST -> compiled Sigma -> validation/proof -> human review
```

## 5. Operating modes

The system supports two execution modes.

### Auto mode

Auto mode runs the pipeline to the final human review gate unless a hard gate fails. It may refine bounded failures, but it must not bypass validation, proof obligations, or human approval.

### Cautious mode

Cautious mode pauses when:

- DetectionSpec requires human approval.
- Evidence, ATT&CK mapping, telemetry grounding, proof obligation, or ranking confidence is below the active profile threshold.
- A required proof obligation is unknown or failed.
- Oracle or regression gates conflict with the candidate.

## 6. Evidence graph

The evidence graph is the central structured representation of report understanding and rule lineage.

Required node types include:

- Report.
- Chunk.
- EvidenceQuote.
- Behavior.
- Entity.
- IOC.
- Tool.
- Malware.
- CVE.
- ATTACKTechnique.
- DetectionStrategy.
- Analytic.
- DataComponent.
- TelemetrySource.
- TelemetryField.
- DetectionHypothesis.
- DetectionSpec.
- DetectionLogicNode.
- RuleCandidate.
- ValidationResult.
- ProofObligation.
- OracleExpectation.
- ReviewDecision.
- FeedbackPattern.
- RegressionTest.

Required edge types include:

- supports.
- mentions.
- maps_to.
- requires.
- implements.
- validated_by.
- derived_from.
- contradicts.
- satisfies.
- failed_by.

Every important artifact must be reachable through lineage from report/chunk evidence to final rule candidate and review decision.

## 7. ATT&CK detection modeling

The graph must not center on the deprecated ATT&CK Data Source abstraction. The required modeling path is:

```text
ATT&CK Technique
  -> Detection Strategy
  -> Analytic
  -> Data Component
  -> Telemetry Source
  -> Telemetry Field
```

Example:

```text
Behavior: encoded PowerShell command execution
  -> Technique: T1059.001 PowerShell
  -> Detection Strategy: command-line behavior detection
  -> Analytic: suspicious encoded command invocation
  -> Data Component: Process Creation
  -> Telemetry Source: Sysmon Event ID 1 / Windows Security 4688
  -> Fields: Image, CommandLine, ParentImage, OriginalFileName
  -> Logic: CommandLine contains encoded-command indicators
```

This model must support both ATT&CK-aligned reasoning and local telemetry validation.

## 8. Retrieval and citation faithfulness

Retrieval should evolve in layers:

1. Deterministic chunking and lexical retrieval.
2. BM25 retrieval.
3. Dense embedding retrieval.
4. Reciprocal Rank Fusion.
5. Section-aware context selection.
6. Graph-neighbor expansion.
7. Reranking.

Citation verification is a hard gate. For each evidence quote:

- `chunk_id` must exist.
- `quote` must exactly match chunk text.
- `start_offset` and `end_offset` must match the exact quote span.
- Claims derived from the quote must be supported by the quote.

A citation mismatch is a hard failure, not a warning.

## 9. Controlled multi-agent layer

Agents are specialized and orchestrated stage-by-stage. They do not engage in free-form unbounded debate.

Primary agent roles:

- Evidence Agent.
- Entity/IOC Agent.
- Behavior Hypothesis Agent.
- ATT&CK Mapping Agent.
- Detection Strategy/Analytic Mapping Agent.
- Telemetry Grounding Agent.
- DetectionSpec Agent.
- Detection Logic Agent.
- Rule Portfolio Agent.
- Critic Agent.
- Refinement Agent.
- Ranking Agent.
- Review Assistant Agent.

Each agent follows this pattern:

```text
strict input schema -> agent -> strict output schema -> validator -> persistence -> gate decision
```

Every agent run must persist:

- Run id.
- Agent name.
- Input artifact ids.
- Input payload snapshot.
- Output payload snapshot.
- Input/output hashes.
- Prompt version.
- Model id.
- Tokens in/out.
- Latency.
- Cost if available.
- Retry count.
- Terminal status.

One strongest model is used for all agents in the first implementation track.

## 10. Formal DetectionSpec

DetectionSpec is the mandatory intermediate representation. It must contain:

- Evidence ids.
- Behavior ids.
- ATT&CK technique mappings.
- Detection strategies.
- Analytics.
- Data components.
- Telemetry requirements.
- Allowed telemetry fields.
- Detection logic requirements.
- False-positive hypotheses.
- Test plan.
- Abstain reason when generation is unsafe.

The DetectionSpec verifier must enforce:

- Every behavior has evidence.
- Every ATT&CK mapping has evidence.
- Every analytic has a data component.
- Every telemetry field is allowed by registry.
- Every detection condition traces to evidence or telemetry rationale.
- No production rule can be generated without a verified DetectionSpec.
- Abstain is required when evidence or telemetry is insufficient.

## 11. Proof obligations

Rule candidates must carry proof obligations. Validators check outputs; proof obligations require candidates to prove the claims that make them selectable.

Required proof obligation types include:

- `detects_report_behavior`: the rule detects the behavior described by report evidence.
- `not_overbroad`: the rule does not match broad benign behavior beyond threshold.
- `telemetry_fields_exist`: all used fields exist in selected telemetry.
- `positive_tests_pass`: expected positive events are matched.
- `benign_baseline_not_matched`: must-not-match benign events are not matched beyond threshold.
- `citation_faithful`: evidence citations are exact and claim-supporting.
- `oracle_expectations_satisfied`: oracle expectations pass when oracle data exists.
- `regression_safe`: previous accepted/rejected behavior regressions pass.

Each proof obligation status is one of:

- proven.
- failed.
- unknown.
- not_applicable.

`not_applicable` requires an explicit justification. Final candidates cannot be selected while required proof obligations are failed or unknown.

## 12. Detection-as-code compiler

LLMs should not be the source of final Sigma YAML when a deterministic path is possible. The preferred path is:

```text
DetectionSpec -> Detection Logic AST -> Sigma AST -> Sigma YAML
```

The compiler must enforce:

- Only allowed fields are emitted.
- Sigma logsource matches selected telemetry.
- Detection conditions are structurally sane.
- Metadata is complete.
- Generated rule versions are immutable.

This design enables future translators for KQL, SPL, Elastic EQL, and other backends.

## 13. Rule portfolio

The system generates a portfolio, not a single rule.

Initial candidate types:

- high_precision.
- balanced.
- high_recall.
- behavior_only.
- ioc_assisted.
- telemetry_specific.
- correlation_optional.

Each candidate must include:

- Candidate type.
- Expected precision/recall tradeoff.
- Required telemetry.
- Evidence support.
- Known limitations.
- Proof obligations.
- Validation status.
- Score breakdown.

Only candidates passing required gates enter final ranking.

## 14. Static validation

Static validation gates include:

- Sigma syntax and structure validity.
- Field allowed check.
- Logsource compatibility.
- ATT&CK tag validity.
- Evidence linkage.
- Broad-rule detection.
- Condition sanity.
- False-positive notes presence.
- Metadata completeness.

Static validation failure either triggers bounded refinement or removes the candidate.

## 15. Dynamic, adversarial, and counterfactual evaluation

Dynamic validation uses:

- Positive synthetic logs.
- Negative benign logs.
- Edge-case logs.
- Replay logs when available.

Adversarial validation tests rule robustness against variants such as:

- Renamed binaries.
- Command obfuscation.
- Parent process variation.
- Alternative LOLBins.
- Network destination variation.
- Case/path variation.
- Missing optional fields.

Counterfactual evaluation mutates rule conditions to determine condition importance, precision/recall impact, and overfitting risk.

Candidate evaluation should produce:

- True-positive estimate.
- False-positive estimate.
- Robustness score.
- Bypass sensitivity.
- Telemetry dependency risk.
- Condition importance summary.

## 16. Oracle evaluation

When oracle data exists, it is authoritative for evaluation.

Oracle cases include:

- Expected techniques.
- Expected behaviors.
- Expected telemetry.
- Expected positive event ids.
- Must-not-match benign event ids.
- Expected logic family.
- Acceptable rule formats.

Oracle evaluation checks:

- Technique mapping correctness.
- Telemetry correctness.
- Logic family correctness.
- Positive event matching.
- Benign event avoidance.
- Evidence citation correctness.

Internal oracle fixtures come first. CTI-REALM integration is a later benchmark adapter.

## 17. Ranking

Final ranking is multi-objective. The score must include:

- Evidence support score.
- Citation faithfulness score.
- Telemetry fit score.
- Static validity score.
- Dynamic precision score.
- Dynamic recall score.
- Adversarial robustness score.
- Oracle score when available.
- Regression safety score.
- Readability score.
- False-positive risk penalty.
- Complexity penalty.
- Unsupported-claim penalty.

Profiles influence ranking:

- strict: prioritize precision, citation faithfulness, proof completion, and low false positives.
- balanced: balance precision, recall, robustness, and usability.
- exploratory: prioritize recall and hunting usefulness, but still require citation faithfulness and telemetry validity.

## 18. Human review

Human review remains mandatory before export. The UI must show enough information for fast expert review:

- Best candidate.
- Rejected candidates.
- Evidence quotes.
- Evidence graph path.
- DetectionSpec.
- Detection logic AST.
- Sigma rule.
- Proof obligation status.
- Static/dynamic/adversarial/oracle results.
- False-positive hypotheses.
- Known limitations.
- Suggested edits.

Review actions include:

- accept.
- reject.
- edit.
- make stricter.
- make broader.
- prefer behavior-based.
- allow hunting-only artifact.
- abstain.

## 19. Feedback learning and Detection CI/CD regression

Feedback must become regression tests, not just memory.

Feedback examples:

- Rejected overbroad pattern.
- Accepted rule pattern.
- Manual edit diff.
- False-positive reason.
- Preferred telemetry source.
- Preferred Sigma metadata style.

Regression gates include:

- Previously rejected patterns must not reappear unless required new constraints are present.
- Accepted rules must still compile and pass validation.
- Accepted proof obligations must remain proven.
- Mutation score must not decrease below threshold.
- False-positive rate must not increase beyond threshold.
- Coverage must not decrease beyond threshold.
- Citation mismatch count must remain zero.

This turns user review into a mechanism that prevents repeated mistakes.

## 20. Persistence model

The backend must persist full audit trail across these layers:

- Report ingestion: `reports`, `report_chunks`.
- Retrieval: `retrieval_queries`, `retrieval_results`.
- Agent audit: `agent_runs`.
- Evidence graph: `graph_nodes`, `graph_edges`, `evidence_quotes`, `behaviors`, `entities`, `iocs`.
- ATT&CK detection model: `attack_techniques`, `detection_strategies`, `analytics`, `data_components`, `technique_detection_links`.
- Telemetry: `telemetry_sources`, `telemetry_fields`, `environment_telemetry_profile`, `telemetry_mappings`.
- DetectionSpec: `detection_specs`, `detection_logic_nodes`, `detection_ast_versions`.
- Proof: `proof_obligations`, `proof_evidence_links`, `proof_verification_results`.
- Rules: `rule_candidates`, `rule_candidate_versions`, `compiled_sigma_rules`, `candidate_scores`.
- Validation: `static_validation_results`, `dynamic_test_cases`, `dynamic_test_runs`, `adversarial_test_cases`, `adversarial_test_runs`, `counterfactual_variants`, `counterfactual_results`.
- Oracle: `oracle_cases`, `oracle_expectations`, `oracle_evaluation_results`.
- Review and learning: `review_decisions`, `manual_edits`, `feedback_patterns`, `regression_tests`, `regression_runs`, `quality_snapshots`.

Generated rules are immutable. Edits create new versions.

## 21. Backend module layout

Target backend structure:

```text
src/de_forge/
  api/routes/
  agents/
  core/
  db/
  models/
  schemas/
  services/
  ui_support/
```

API routes are thin. Business logic belongs in services. Agents produce structured outputs. Services validate, persist, and orchestrate. Schemas define contracts. Models define persistence.

## 22. Minimal UI direction

The initial UI should be minimal but trust-oriented.

Required pages:

- Reports.
- Run Detail.
- Evidence Graph.
- DetectionSpec.
- Rule Portfolio.
- Proof and Validation.
- Human Review.
- Regression History.

The most important screen is rule review, showing:

```text
Evidence quote | Detection logic | Sigma condition | Proof status | Validation score
```

## 23. Build phases

Implementation should proceed in this order:

1. Project reality alignment and this design spec.
2. Deterministic foundation: hashing, idempotency, DB/session, artifact lineage.
3. Evidence graph core.
4. Ingestion, chunking, retrieval, citation verifier.
5. ATT&CK Detection Strategy / Analytic / Data Component registry and telemetry registry.
6. Formal DetectionSpec contract and verifier.
7. Proof obligations.
8. Detection AST and Sigma compiler.
9. Static validation and rule portfolio.
10. Dynamic, adversarial, and counterfactual evaluation.
11. Oracle evaluation.
12. Controlled LLM agents.
13. Orchestrator and auto/cautious modes.
14. Minimal Web UI.
15. Feedback learning and Detection CI/CD regression.
16. Quality dashboard and future benchmark adapter.

The first golden path should be:

```text
English TXT report
  -> PowerShell encoded command behavior
  -> T1059.001
  -> process creation data component
  -> Sysmon EID 1 / Windows Security 4688
  -> verified DetectionSpec
  -> high-precision Sigma candidate
  -> static validation
  -> proof obligations
  -> human review
```

## 24. Final candidate selection rule

A final candidate may be selected only when:

- Citation faithfulness is 100%.
- DetectionSpec is verified.
- Telemetry fields are valid.
- Sigma compiles.
- Static validation passes.
- Required dynamic validation passes or is explicitly unavailable with reduced confidence and human review.
- Required proof obligations are proven.
- Oracle score passes when oracle data exists.
- Regression gates pass.
- Human review approves export.

If these requirements cannot be satisfied, the system must refine within bounded limits, abstain, or produce a hunting-only artifact with explicit limitations.

## 25. Success criteria

The system is successful when it can:

- Run an English TXT/PDF threat report through the full pipeline to human review.
- Produce a Sigma candidate only through the verified DetectionSpec and compiler path.
- Trace every rule condition back to evidence, telemetry rationale, or a verified registry.
- Prove required proof obligations for selected candidates.
- Reject or abstain on unsupported, overbroad, or telemetry-invalid candidates.
- Preserve full audit trail for debugging and review.
- Convert reviewer feedback into regression gates that prevent repeated mistakes.

## 26. Design invariants

These invariants must not be broken:

1. No raw-report-to-production-rule path.
2. DetectionSpec is mandatory before rule generation.
3. Evidence citations must be exact and verified.
4. ATT&CK detection modeling uses Detection Strategy / Analytic / Data Component / Telemetry Source / Field.
5. Required proof obligations must be proven before final selection.
6. Rule generation uses Detection AST and compiler when possible.
7. Human review is mandatory before export.
8. Agent loops are bounded.
9. Feedback must produce regression protection.
10. Full lineage and auditability are mandatory.
