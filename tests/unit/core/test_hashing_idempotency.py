from de_forge.core.hashing import canonicalize_payload, snapshot_hash, verify_snapshot_hash
from de_forge.core.idempotency import make_idempotency_key


def test_canonical_json_sorts_keys_and_removes_whitespace() -> None:
    payload = {"b": 2, "a": {"d": 4, "c": 3}}
    assert canonicalize_payload(payload) == '{"a":{"c":3,"d":4},"b":2}'


def test_snapshot_hash_is_stable_for_equivalent_payloads() -> None:
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert snapshot_hash(left) == snapshot_hash(right)


def test_verify_snapshot_hash_detects_tampering() -> None:
    payload = {"claim": "safe"}
    digest = snapshot_hash(payload)
    assert verify_snapshot_hash(payload, digest) is True
    assert verify_snapshot_hash({"claim": "changed"}, digest) is False


def test_idempotency_key_includes_stage_identifier() -> None:
    payload = {"report_id": "r1", "stage": "ingest"}
    ingest_key = make_idempotency_key("ingestion.chunk", payload)
    evidence_key = make_idempotency_key("evidence.extract", payload)
    assert ingest_key.startswith("idem_")
    assert evidence_key.startswith("idem_")
    assert ingest_key != evidence_key


def test_idempotency_key_is_deterministic_for_same_payload() -> None:
    first = make_idempotency_key("stage", {"b": 2, "a": 1})
    second = make_idempotency_key("stage", {"a": 1, "b": 2})
    assert first == second
