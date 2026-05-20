import hashlib
import json
from typing import Any


def _canonicalize(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_idempotency_key(stage_identifier: str, payload: Any) -> str:
    canonical = _canonicalize(payload)
    digest = hashlib.sha256(f"{stage_identifier}|{canonical}".encode("utf-8")).hexdigest()
    return f"idem_{digest}"
