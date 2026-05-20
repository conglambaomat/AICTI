"""Pure gate predicates for orchestration decisions."""

from collections.abc import Mapping

REQUIRED_LINEAGE_FIELDS: tuple[str, ...] = (
    "report_id",
    "trace_id",
    "run_id",
    "agent_run_id",
)


def can_generate_rule(spec_status: str) -> bool:
    """Return True only when detection spec status is validated."""
    return spec_status == "validated"


def has_required_lineage_fields(lineage: Mapping[str, str]) -> bool:
    """Return True when all required lineage fields exist and are non-blank strings."""
    for field in REQUIRED_LINEAGE_FIELDS:
        value = lineage.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    return True
