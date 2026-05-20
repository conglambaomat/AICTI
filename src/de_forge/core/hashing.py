import hashlib
import json
from typing import Any


def snapshot_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_snapshot_hash(payload: Any, expected_hash: str) -> bool:
    return snapshot_hash(payload) == expected_hash
