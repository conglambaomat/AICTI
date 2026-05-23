"""Schema contracts for memory runtime interactions."""

from __future__ import annotations

from pydantic import BaseModel


class MemoryAccessRequest(BaseModel):
    role: str
    namespace: str
    operation: str
    stage: str
    run_state: str


class MemoryAccessDecision(BaseModel):
    allowed: bool
