import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main

CASES = json.loads((Path(__file__).parent / "acceptance_cases.json").read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "brandlens-test.sqlite3")
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_and_seeded_demo(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    review = client.get("/api/reviews/BL-DEMO-001")
    assert review.status_code == 200
    assert review.json()["findings"]
    assert all(f["source_id"] and f["source_label"] for f in review.json()["findings"])


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_labelled_acceptance_cases(client, case):
    payload = {
        "title": case["id"],
        "channel": case.get("channel", "Test channel"),
        "product_scope": case.get("product_scope", "Not specified"),
        "draft_text": case["text"],
        "created_by": "Acceptance test"
    }
    response = client.post("/api/reviews", json=payload)
    assert response.status_code == 201
    review = response.json()
    titles = [f["title"] for f in review["findings"]]
    if case["expect"] is None:
        assert titles == [], f"{case['id']} should have no finding, got {titles}"
    else:
        assert case["expect"] in titles, f"{case['id']} expected {case['expect']}, got {titles}"
        assert all(f["source_id"] and f["source_label"] for f in review["findings"])


def test_accept_does_not_silently_edit_draft(client):
    review = client.get("/api/reviews/BL-DEMO-001").json()
    original_text = review["draft_text"]
    finding = review["findings"][0]
    response = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "accept", "actor": "Demo creator", "actor_role": "Creator", "finding_id": finding["id"]
    })
    assert response.status_code == 200
    assert response.json()["draft_text"] == original_text
    assert any(f["status"] == "accepted" for f in response.json()["findings"])


def test_dispute_requires_reason_and_is_audited(client):
    review = client.get("/api/reviews/BL-DEMO-001").json()
    finding = review["findings"][0]
    missing_reason = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "dispute", "actor": "Demo creator", "actor_role": "Creator", "finding_id": finding["id"]
    })
    assert missing_reason.status_code == 422
    response = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "dispute", "actor": "Demo creator", "actor_role": "Creator", "finding_id": finding["id"], "reason": "This wording is intentional for review."
    })
    assert response.status_code == 200
    assert any(f["status"] == "disputed" for f in response.json()["findings"])
    audit = client.get(f"/api/reviews/{review['id']}/audit").json()
    assert any(e["event_type"] == "finding_disputed" for e in audit)


def test_role_restrictions_and_approval_override(client):
    review = client.get("/api/reviews/BL-DEMO-001").json()
    creator_approve = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "approve", "actor": "Demo creator", "actor_role": "Creator"
    })
    assert creator_approve.status_code == 403
    reviewer_approve_without_reason = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "approve", "actor": "Demo reviewer", "actor_role": "Reviewer"
    })
    assert reviewer_approve_without_reason.status_code == 409
    reviewer_approve_with_reason = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "approve", "actor": "Demo reviewer", "actor_role": "Reviewer", "reason": "Manual override for workflow test."
    })
    assert reviewer_approve_with_reason.status_code == 200
    assert reviewer_approve_with_reason.json()["status"] == "approved"


def test_edit_creates_new_version_and_rescans(client):
    review = client.get("/api/reviews/BL-DEMO-001").json()
    response = client.post(f"/api/reviews/{review['id']}/actions", json={
        "action": "edit", "actor": "Demo creator", "actor_role": "Creator",
        "draft_text": "Our skincare product supports hydration for everyday use."
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated["current_version"] == review["current_version"] + 1
    assert updated["draft_text"].startswith("Our skincare product")
    audit = client.get(f"/api/reviews/{review['id']}/audit").json()
    assert any(e["event_type"] == "revision" and e["version_no"] == updated["current_version"] for e in audit)


def test_claim_validation(client):
    response = client.post("/api/claims", json={
        "claim": "Test statement long enough", "product_scope": "Demo product", "channel_scope": "Web",
        "evidence_source": "Memo 123", "approver": "Reviewer", "valid_from": "2026-11-01",
        "valid_until": "2026-10-01", "note": "invalid dates", "actor_role": "Admin"
    })
    assert response.status_code == 422


def test_dashboard_claims_rules_insights_and_static_ui(client):
    assert client.get("/").status_code == 200
    assert "BrandLens" in client.get("/").text
    assert len(client.get("/api/claims").json()) >= 3
    assert len(client.get("/api/rules").json()) >= 4
    insights = client.get("/api/insights")
    assert insights.status_code == 200
    assert "rule_clusters" in insights.json()
    assert "audit" in insights.json()


def test_submit_and_claim_creation_demo_roles(client):
    denied = client.post("/api/reviews", json={
        "title": "Manager draft", "channel": "Social", "product_scope": "LumaSkin Serum",
        "draft_text": "A safe simple statement.", "created_by": "Demo manager", "actor_role": "Manager"
    })
    assert denied.status_code == 403
    claim = {
        "claim": "A fictional approved hydration statement.", "product_scope": "Demo gel", "channel_scope": "Social",
        "evidence_source": "Fictional memo TEST-01", "approver": "Demo admin", "valid_from": "2026-01-01",
        "valid_until": "2027-01-01", "note": "seeded test record"
    }
    denied_claim = client.post("/api/claims", json={**claim, "actor_role": "Creator"})
    assert denied_claim.status_code == 403
    allowed_claim = client.post("/api/claims", json={**claim, "actor_role": "Admin"})
    assert allowed_claim.status_code == 201
    assert allowed_claim.json()["claim"].startswith("A fictional approved")
