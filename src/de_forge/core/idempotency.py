import hashlib

from de_forge.core.constants import IDEMPOTENCY_KEY_PREFIX
from de_forge.core.hashing import JsonValue, canonicalize_payload


def make_idempotency_key(stage_identifier: str, payload: JsonValue) -> str:
    """Build a deterministic idempotency key for a pipeline stage input.

    Args:
        stage_identifier: Stable stage name to scope idempotency.
        payload: JSON-compatible value used as stage input.

    Returns:
        Prefixed SHA-256-based idempotency key.

    Raises:
        TypeError: If payload contains non-JSON-serializable values.
        ValueError: If payload contains NaN or infinity.
    """
    canonical = canonicalize_payload(payload)
    digest = hashlib.sha256(f"{stage_identifier}|{canonical}".encode()).hexdigest()
    return f"{IDEMPOTENCY_KEY_PREFIX}{digest}"
