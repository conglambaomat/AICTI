import pytest

from de_forge.core.hashing import JsonValue, snapshot_hash, verify_snapshot_hash
from de_forge.core.idempotency import make_idempotency_key


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    payload: JsonValue = {"b": 2, "a": 1}
    key1 = make_idempotency_key("stage.ingest", payload)
    key2_payload: JsonValue = {"a": 1, "b": 2}
    key2 = make_idempotency_key("stage.ingest", key2_payload)
    assert key1 == key2


def test_idempotency_key_changes_with_stage_identifier() -> None:
    payload: JsonValue = {"a": 1, "b": 2}
    key_ingest = make_idempotency_key("stage.ingest", payload)
    key_extract = make_idempotency_key("stage.extract", payload)
    assert key_ingest != key_extract


def test_make_idempotency_key_rejects_nan_and_infinity() -> None:
    with pytest.raises(ValueError):
        bad: JsonValue = {"v": float("nan")}
        make_idempotency_key("stage.ingest", bad)

    with pytest.raises(ValueError):
        bad_inf: JsonValue = {"v": float("inf")}
        make_idempotency_key("stage.ingest", bad_inf)


def test_make_idempotency_key_rejects_non_serializable_input() -> None:
    with pytest.raises(TypeError):
        bad_non_serializable: object = {"bad": {1, 2, 3}}
        make_idempotency_key("stage.ingest", bad_non_serializable)  # type: ignore[arg-type]


def test_snapshot_hash_is_deterministic_for_equivalent_payloads() -> None:
    left: JsonValue = {"b": 2, "a": 1}
    right: JsonValue = {"a": 1, "b": 2}
    digest1 = snapshot_hash(left)
    digest2 = snapshot_hash(right)

    assert digest1 == digest2


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload: JsonValue = {"x": "safe"}
    assert verify_snapshot_hash(payload, "bad-hash") is False


def test_verify_snapshot_hash_passes_for_matching_hash() -> None:
    payload: JsonValue = {"x": "safe"}
    digest = snapshot_hash(payload)
    assert verify_snapshot_hash(payload, digest) is True
