from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from de_forge.main import app

client = TestClient(app)


def test_post_review_approval() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "approved",
            "comments": "Looks good",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["review_id"]
    assert body["run_id"] == run_id
    assert body["decision"] == "approved"


def test_post_review_rejection() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "rejected",
            "comments": "False positive risk too high",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["decision"] == "rejected"



def test_post_review_rejects_invalid_decision() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/reviews",
        json={
            "run_id": run_id,
            "reviewer": "analyst@example.com",
            "decision": "maybe",
            "comments": "Invalid review decision.",
        },
    )

    assert response.status_code == 422


def test_export_sigma_requires_approval() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]
    rule_id = seed.json()["rule_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    handoff = client.post(f"/v1/pipeline:reject?rule_id={rule_id}&run_id={run_id}")
    assert handoff.status_code == 201

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 403
    body = response.json()
    assert "approval" in body["detail"].lower()


def test_export_sigma_requires_review_handoff_memory() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 403
    assert "handoff" in response.json()["detail"].lower()


def test_export_sigma_success() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]
    rule_id = seed.json()["rule_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={run_id}")
    assert approve.status_code == 201

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rule_id"] == rule_id
    assert body["format"] == "sigma"
    assert body["content"]


def test_export_sigma_blocked_when_latest_decision_is_rejected() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]
    rule_id = seed.json()["rule_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={run_id}")
    assert approve.status_code == 201

    reject = client.post(f"/v1/pipeline:reject?rule_id={rule_id}&run_id={run_id}")
    assert reject.status_code == 201

    response = client.post(
        "/v1/exports/sigma",
        json={"run_id": run_id},
    )

    assert response.status_code == 403
    body = response.json()
    assert "approval" in body["detail"].lower()


def test_export_sigma_uses_requested_run_proof_state() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    first_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert first_run.status_code == 200
    first_body = first_run.json()
    first_run_id = first_body["run_id"]
    rule_id = first_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={first_run_id}")
    assert approve.status_code == 201

    second_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert second_run.status_code == 200
    second_run_id = second_run.json()["run_id"]

    second_approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={second_run_id}")
    assert second_approve.status_code == 201

    from de_forge.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE proof_obligations
                SET status = 'unknown', justification = NULL
                WHERE run_id = :run_id AND rule_candidate_id = :rule_id
                """
            ),
            {"run_id": second_run_id, "rule_id": rule_id},
        )
        db.commit()
    finally:
        db.close()

    first_export = client.post("/v1/exports/sigma", json={"run_id": first_run_id})
    assert first_export.status_code == 200

    second_export = client.post("/v1/exports/sigma", json={"run_id": second_run_id})
    assert second_export.status_code == 403
    assert "proof obligation" in second_export.json()["detail"].lower()


def test_export_sigma_rejects_approval_from_different_run() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    first_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert first_run.status_code == 200
    first_body = first_run.json()
    first_run_id = first_body["run_id"]
    rule_id = first_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={first_run_id}")
    assert approve.status_code == 201

    second_run = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert second_run.status_code == 200
    second_run_id = second_run.json()["run_id"]

    response = client.post("/v1/exports/sigma", json={"run_id": second_run_id})

    assert response.status_code == 403
    assert "handoff" in response.json()["detail"].lower()


def test_export_sigma_fails_closed_when_requested_run_proofs_are_missing() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={run_id}")
    assert approve.status_code == 201

    from de_forge.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                DELETE FROM proof_obligations
                WHERE run_id = :run_id AND rule_candidate_id = :rule_id
                """
            ),
            {"run_id": run_id, "rule_id": rule_id},
        )
        db.commit()
    finally:
        db.close()

    response = client.post("/v1/exports/sigma", json={"run_id": run_id})

    assert response.status_code == 403
    assert "proof obligation" in response.json()["detail"].lower()


def test_export_sigma_blocks_non_awaiting_review_run() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={run_id}")
    assert approve.status_code == 201

    from de_forge.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE pipeline_runs
                SET status = 'failed', stage = 'static_validation_failed'
                WHERE run_id = :run_id
                """
            ),
            {"run_id": run_id},
        )
        db.commit()
    finally:
        db.close()

    response = client.post("/v1/exports/sigma", json={"run_id": run_id})

    assert response.status_code == 403
    assert "approval" in response.json()["detail"].lower()


def test_export_sigma_blocks_not_applicable_requested_run_proofs() -> None:
    seed = client.post("/v1/pipeline:seed")
    assert seed.status_code == 201
    report_id = seed.json()["report_id"]

    run_response = client.post(
        "/v1/pipeline:run",
        json={"report_id": report_id, "profile": "balanced"},
    )
    assert run_response.status_code == 200
    run_body = run_response.json()
    run_id = run_body["run_id"]
    rule_id = run_body["rule_id"]

    approve = client.post(f"/v1/pipeline:approve?rule_id={rule_id}&run_id={run_id}")
    assert approve.status_code == 201

    from de_forge.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE proof_obligations
                SET status = 'not_applicable', justification = 'manual waiver'
                WHERE run_id = :run_id AND rule_candidate_id = :rule_id
                """
            ),
            {"run_id": run_id, "rule_id": rule_id},
        )
        db.commit()
    finally:
        db.close()

    response = client.post("/v1/exports/sigma", json={"run_id": run_id})

    assert response.status_code == 403
    assert "proof obligation" in response.json()["detail"].lower()
