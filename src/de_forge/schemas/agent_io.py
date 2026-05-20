"""Agent I/O contracts enforcing DetectionSpec-first gate."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from de_forge.schemas.detection_spec import DetectionSpec


class RuleGenerationRequest(BaseModel):
    """Input contract for rule generation requiring validated DetectionSpec."""

    model_config = ConfigDict(extra="forbid")

    detection_spec: DetectionSpec
    target_format: Literal["sigma", "kql"]
