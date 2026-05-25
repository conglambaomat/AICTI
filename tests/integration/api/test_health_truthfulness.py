from fastapi.testclient import TestClient

from de_forge import main
from de_forge.main import app


def test_health_separates_measured_checks_from_static_policy() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()

    assert "checks" in body
    assert "policy" in body
    assert "details" in body
    assert "policy" not in body["details"]
    assert body["checks"].keys() == {"api", "database", "schema"}
    assert body["policy"] == {
        "human_review_required_for_export": True,
        "detection_spec_required": True,
        "proof_obligation_required": True,
        "citation_exact_required": True,
        "raw_report_to_rule_forbidden": True,
        "agent_loops_bounded": True,
    }


def test_health_fails_closed_when_database_probe_fails(monkeypatch) -> None:
    def fail_database_probe() -> None:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(main, "check_database_connection", fail_database_probe)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["readiness"] == "not_ready"
    assert body["checks"]["database"] == "failed"
    assert body["checks"]["schema"] == "failed"
    assert body["details"]["db_probe"] is None
    assert "database_probe_failed" in body["errors"]


def test_health_fails_closed_when_schema_guard_raises_unexpected_error(monkeypatch) -> None:
    def pass_database_probe() -> None:
        return None

    class BrokenSchemaGuard:
        def __init__(self, engine: object) -> None:
            pass

        def assert_contract_current(self) -> None:
            raise RuntimeError("schema unavailable")

    monkeypatch.setattr(main, "check_database_connection", pass_database_probe)
    monkeypatch.setattr(main, "SchemaGuard", BrokenSchemaGuard)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["readiness"] == "not_ready"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["schema"] == "failed"
    assert body["details"]["db_probe"] == "select_1"
    assert body["details"]["schema_guard"] == "drift_or_unavailable"
    assert "schema_probe_failed" in body["errors"]
