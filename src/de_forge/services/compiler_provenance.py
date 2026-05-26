"""Compiler provenance validation for generated rules."""

from typing import Protocol


class CompilerProvenanceError(ValueError):
    """Raised when a rule lacks required compiler provenance."""


class RuleWithCompilerProvenance(Protocol):
    """Protocol for rule objects with compiler provenance fields."""

    id: str
    generation_source: str
    detection_ast_id: object
    compiled_sigma_id: object


class CompilerProvenanceService:
    """Validate that rules were produced by the compiler pipeline."""

    @staticmethod
    def assert_rule_has_compiler_provenance(rule: RuleWithCompilerProvenance) -> None:
        """Raise when a rule lacks compiler provenance.

        Args:
            rule: Rule-like object exposing generation_source, detection_ast_id,
                and compiled_sigma_id attributes.

        Raises:
            CompilerProvenanceError: If the rule is not compiler-generated or
                lacks required compiler lineage fields.
        """
        if rule.generation_source != "compiler":
            raise CompilerProvenanceError("Rule is not compiler-generated")
        if not rule.detection_ast_id:
            raise CompilerProvenanceError("Rule is missing Detection AST provenance")
        if not rule.compiled_sigma_id:
            raise CompilerProvenanceError("Rule is missing compiled Sigma provenance")

        rule_id = getattr(rule, "id", None)
        if rule_id is not None:
            if rule.detection_ast_id == f"ast-{rule_id}":
                raise CompilerProvenanceError("Rule uses placeholder Detection AST provenance")
            if rule.compiled_sigma_id == f"sigma-{rule_id}":
                raise CompilerProvenanceError("Rule uses placeholder compiled Sigma provenance")
