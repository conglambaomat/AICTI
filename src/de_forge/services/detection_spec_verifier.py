from __future__ import annotations

from de_forge.core.errors import ValidationGateError
from de_forge.schemas.detection_spec import DetectionSpec
from de_forge.services.telemetry_registry import is_supported_telemetry_type


class DetectionSpecVerifier:
    def verify(self, spec: DetectionSpec) -> bool:
        if not spec.behavior_rules:
            raise ValidationGateError("DetectionSpec requires behavior rules")

        for rule in spec.behavior_rules:
            for telemetry in rule.required_telemetry:
                if not is_supported_telemetry_type(telemetry):
                    raise ValidationGateError(f"unsupported telemetry type: {telemetry}")

        return True
