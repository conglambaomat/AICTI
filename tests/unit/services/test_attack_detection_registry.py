from de_forge.services.attack_detection_registry import AttackDetectionRegistry


def test_attack_registry_maps_known_technique() -> None:
    registry = AttackDetectionRegistry.default()

    links = registry.links_for_technique("T1059.001")

    assert len(links) >= 1
    assert links[0].technique_id == "T1059.001"
    assert links[0].detection_strategy_id == "ds_command_line_behavior"
    assert links[0].analytic_id == "analytic_encoded_powershell"
    assert links[0].data_component_id == "process_creation"
