import pytest

from de_forge.core.idempotency import make_idempotency_key
from de_forge.core.hashing import verify_snapshot_hash


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    payload = {"b": 2, "a": 1}
    key1 = make_idempotency_key("stage.ingest", payload)
    key2 = make_idempotency_key("stage.ingest", {"a": 1, "b": 2})
    assert key1 == key2


def test_idempotency_key_changes_with_stage_identifier() -> None:
    payload = {"a": 1, "b": 2}
    key_ingest = make_idempotency_key("stage.ingest", payload)
    key_extract = make_idempotency_key("stage.extract", payload)
    assert key_ingest != key_extract


def test_make_idempotency_key_rejects_nan_and_infinity() -> None:
    with pytest.raises(ValueError):
        make_idempotency_key("stage.ingest", {"v": float("nan")})

    with pytest.raises(ValueError):
        make_idempotency_key("stage.ingest", {"v": float("inf")})


def test_make_idempotency_key_rejects_non_serializable_input() -> None:
    with pytest.raises(TypeError):
        make_idempotency_key("stage.ingest", {"bad": {1, 2, 3}})


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload = {"x": "safe"}
    assert verify_snapshot_hash(payload, "bad-hash") is False
