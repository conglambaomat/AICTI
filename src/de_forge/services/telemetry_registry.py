"""Telemetry registry for MVP allowed telemetry and fields."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetryRegistryEntry:
    """Registry entry for a telemetry type allowlist."""

    telemetry_type: str
    allowed_fields: frozenset[str]


PROCESS_CREATION_ALLOWED_FIELDS = frozenset(
    {
        "CommandLine",
        "Image",
        "ParentImage",
        "ParentCommandLine",
        "User",
        "CurrentDirectory",
        "ProcessId",
        "ParentProcessId",
        "IntegrityLevel",
        "LogonGuid",
        "LogonId",
        "Hashes",
        "OriginalFileName",
        "Company",
        "Product",
        "Description",
    }
)

TELEMETRY_REGISTRY: dict[str, TelemetryRegistryEntry] = {
    "process_creation": TelemetryRegistryEntry(
        telemetry_type="process_creation",
        allowed_fields=PROCESS_CREATION_ALLOWED_FIELDS,
    )
}


def is_supported_telemetry_type(telemetry_type: str) -> bool:
    """Return whether telemetry type is supported in MVP registry."""
    return telemetry_type in TELEMETRY_REGISTRY


def validate_required_fields(telemetry_type: str, required_fields: list[str]) -> list[str]:
    """Return fields that are not allowed for the telemetry type."""
    entry = TELEMETRY_REGISTRY.get(telemetry_type)
    if entry is None:
        return required_fields

    return [field for field in required_fields if field not in entry.allowed_fields]
