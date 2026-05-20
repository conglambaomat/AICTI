from de_forge.core.idempotency import make_idempotency_key
from de_forge.core.hashing import verify_snapshot_hash


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    payload = {"b": 2, "a": 1}
    key1 = make_idempotency_key("stage.ingest", payload)
    key2 = make_idempotency_key("stage.ingest", {"a": 1, "b": 2})
    assert key1 == key2


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload = {"x": "safe"}
    assert verify_snapshot_hash(payload, "bad-hash") is False
