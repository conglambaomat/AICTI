"""Integration tests for dynamic validation service."""

from de_forge.services.dynamic_validation import DynamicValidationService

ATTACK_EVENTS = [
    {
        "EventID": 1,
        "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        "CommandLine": "powershell.exe -enc SQBFAFgA",
    },
    {
        "EventID": 1,
        "Image": "C:\\Windows\\System32\\cmd.exe",
        "CommandLine": "cmd.exe /c whoami",
    },
]

BENIGN_EVENTS = [
    {
        "EventID": 1,
        "Image": "C:\\Windows\\System32\\notepad.exe",
        "CommandLine": "notepad.exe",
    },
    {
        "EventID": 1,
        "Image": "C:\\Windows\\explorer.exe",
        "CommandLine": "explorer.exe",
    },
]


def test_dynamic_validation_returns_tp_fp_metrics() -> None:
    """Dynamic validation must produce TP/FP metrics for synthetic corpus."""
    service = DynamicValidationService()

    rule = """title: detect encoded powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
    CommandLine|contains: '-enc'
  condition: selection
"""

    result = service.run_synthetic_validation(
        rule=rule,
        attack_events=ATTACK_EVENTS,
        benign_events=BENIGN_EVENTS,
    )

    assert result.true_positives >= 1
    assert result.false_positives == 0
    assert result.attack_total == len(ATTACK_EVENTS)
    assert result.benign_total == len(BENIGN_EVENTS)


def test_dynamic_validation_result_is_deterministic_for_same_inputs() -> None:
    """Dynamic validation must return deterministic outputs for identical inputs."""
    service = DynamicValidationService()

    rule = """title: detect powershell
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'powershell'
  condition: selection
"""

    result1 = service.run_synthetic_validation(
        rule=rule,
        attack_events=ATTACK_EVENTS,
        benign_events=BENIGN_EVENTS,
    )
    result2 = service.run_synthetic_validation(
        rule=rule,
        attack_events=ATTACK_EVENTS,
        benign_events=BENIGN_EVENTS,
    )

    assert result1 == result2


def test_dynamic_validation_handles_no_matches() -> None:
    """Dynamic validation must handle rules that match nothing."""
    service = DynamicValidationService()

    rule = """title: impossible match
logsource:
  product: windows
  category: process_creation
detection:
  selection:
    Image|contains: 'this-will-not-match'
  condition: selection
"""

    result = service.run_synthetic_validation(
        rule=rule,
        attack_events=ATTACK_EVENTS,
        benign_events=BENIGN_EVENTS,
    )

    assert result.true_positives == 0
    assert result.false_positives == 0
