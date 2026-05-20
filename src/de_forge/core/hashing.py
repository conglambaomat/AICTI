import hashlib
import json
from typing import TypeAlias


JsonPrimitive: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


def canonicalize_payload(payload: JsonValue) -> str:
    """Serialize payload deterministically for hashing/idempotency."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def snapshot_hash(payload: JsonValue) -> str:
    canonical = canonicalize_payload(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_snapshot_hash(payload: JsonValue, expected_hash: str) -> bool:
    return snapshot_hash(payload) == expected_hash
