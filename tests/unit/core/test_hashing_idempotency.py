from de_forge.core.hashing import (
    JsonValue,
    canonicalize_payload,
    snapshot_hash,
    verify_snapshot_hash,
)
from de_forge.core.idempotency import make_idempotency_key


def test_canonical_json_sorts_keys_and_removes_whitespace() -> None:
    payload: JsonValue = {"b": 2, "a": {"d": 4, "c": 3}}
    assert canonicalize_payload(payload) == '{"a":{"c":3,"d":4},"b":2}'


def test_snapshot_hash_is_stable_for_equivalent_payloads() -> None:
    left: JsonValue = {"b": 2, "a": 1}
    right: JsonValue = {"a": 1, "b": 2}
    assert snapshot_hash(left) == snapshot_hash(right)


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload: JsonValue = {"claim": "safe"}
    digest = snapshot_hash(payload)
    assert verify_snapshot_hash(payload, digest) is True
    tampered: JsonValue = {"claim": "changed"}
    assert verify_snapshot_hash(tampered, digest) is False


def test_idempotency_key_includes_stage_identifier() -> None:
    payload: JsonValue = {"report_id": "r1", "stage": "ingest"}
    ingest_key = make_idempotency_key("ingestion.chunk", payload)
    evidence_key = make_idempotency_key("evidence.extract", payload)
    assert ingest_key.startswith("idem_")
    assert evidence_key.startswith("idem_")
    assert ingest_key != evidence_key


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    first_payload: JsonValue = {"b": 2, "a": 1}
    second_payload: JsonValue = {"a": 1, "b": 2}
    first = make_idempotency_key("stage", first_payload)
    second = make_idempotency_key("stage", second_payload)
    assert first == second
