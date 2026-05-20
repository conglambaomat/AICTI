import hashlib

from de_forge.core.constants import IDEMPOTENCY_KEY_PREFIX
from de_forge.core.hashing import JsonValue, canonicalize_payload


def make_idempotency_key(stage_identifier: str, payload: JsonValue) -> str:
    canonical = canonicalize_payload(payload)
    digest = hashlib.sha256(f"{stage_identifier}|{canonical}".encode("utf-8")).hexdigest()
    return f"{IDEMPOTENCY_KEY_PREFIX}{digest}"
