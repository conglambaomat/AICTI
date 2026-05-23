import pytest

from de_forge.services.attack_detection_registry import AttackDetectionRegistry
from de_forge.services.telemetry_registry import field_exists, fields_for_source


def test_attack_registry_maps_technique_to_strategy_chain() -> None:
    registry = AttackDetectionRegistry.default()

    links = registry.links_for_technique("T1059.001")

    assert len(links) >= 1
    assert links[0].technique_id == "T1059.001"
    assert links[0].detection_strategy_id == "ds_command_line_behavior"
    assert links[0].analytic_id == "analytic_encoded_powershell"
    assert links[0].data_component_id == "process_creation"


def test_telemetry_registry_accepts_known_fields() -> None:
    assert field_exists("process_creation", "CommandLine") is True
    assert field_exists("process_creation", "Image") is True


def test_telemetry_registry_rejects_unknown_field() -> None:
    assert field_exists("process_creation", "DefinitelyNotAField") is False


def test_telemetry_registry_requires_known_source() -> None:
    with pytest.raises(KeyError):
        fields_for_source("unknown_source")
