from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SigmaLogsource(BaseModel):
    product: str
    category: str
    service: str | None = None


class SigmaRule(BaseModel):
    title: str
    id: str
    status: str
    description: str
    references: list[str] = Field(default_factory=list)
    tags: list[str]
    logsource: SigmaLogsource
    detection: dict[str, Any]
    falsepositives: list[str]
    level: str
    provenance: dict[str, list[str]]
