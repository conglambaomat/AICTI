import hashlib
import json
from typing import TypeAlias


JsonPrimitive: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


def canonicalize_payload(payload: JsonValue) -> str:
    """Serialize a JSON-compatible payload deterministically.

    Args:
        payload: JSON-compatible value to normalize.

    Returns:
        Canonical JSON string with sorted keys and stable separators.

    Raises:
        TypeError: If payload contains non-JSON-serializable values.
        ValueError: If payload contains NaN or infinity.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def snapshot_hash(payload: JsonValue) -> str:
    """Compute a deterministic SHA-256 hash for a payload snapshot.

    Args:
        payload: JSON-compatible value to hash.

    Returns:
        Hexadecimal SHA-256 digest of the canonical payload representation.

    Raises:
        TypeError: If payload contains non-JSON-serializable values.
        ValueError: If payload contains NaN or infinity.
    """
    canonical = canonicalize_payload(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_snapshot_hash(payload: JsonValue, expected_hash: str) -> bool:
    """Check whether a payload matches an expected snapshot hash.

    Args:
        payload: JSON-compatible value to verify.
        expected_hash: Expected hexadecimal SHA-256 digest.

    Returns:
        True if computed hash matches expected_hash, otherwise False.

    Raises:
        TypeError: If payload contains non-JSON-serializable values.
        ValueError: If payload contains NaN or infinity.
    """
    return snapshot_hash(payload) == expected_hash
