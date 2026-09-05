"""
Integration Smoke Test for End-to-End Incident Lifecycle via FastAPI
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard_summary_endpoint(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue_at_risk_paise" in data
    assert "total_recovered_paise" in data
    assert "recovery_rate" in data


def test_full_incident_simulation_lifecycle(client):
    # 1. Create a new incident
    create_payload = {
        "title": "Integration Test UPI Outage",
        "incident_type": "UPI_TIMEOUT_SPIKE",
        "payment_method": "UPI",
        "severity_pct": 70.0,
        "affected_count": 200,
        "random_seed": 42
    }
    create_res = client.post("/api/incidents", json=create_payload)
    assert create_res.status_code == 200
    incident = create_res.json()
    incident_id = incident["id"]
    assert incident["status"] == "ACTIVE"
    assert incident["revenue_at_risk_paise"] > 0

    # 2. Get Incident Detail
    detail_res = client.get(f"/api/incidents/{incident_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert "health_points" in detail_data
    assert len(detail_data["health_points"]) > 0

    # 3. Execute Recovery on the Incident
    recover_res = client.post(f"/api/incidents/{incident_id}/recover?seed=42")
    assert recover_res.status_code == 200
    rec_data = recover_res.json()
    assert rec_data["status"] == "RESOLVED"
    assert rec_data["recoverai_recovered_paise"] > 0
    assert rec_data["successful_recoveries"] > 0
    assert len(rec_data["replay_steps"]) >= 4

    # 4. Check Replay Steps Endpoint
    replay_res = client.get(f"/api/incidents/{incident_id}/replay")
    assert replay_res.status_code == 200
    steps = replay_res.json()
    assert len(steps) >= 4
    phases = [s["phase"] for s in steps]
    assert "DETECT" in phases
    assert "DIAGNOSE" in phases
    assert "MEASURE" in phases

    # 5. Check Audit Logs
    audit_res = client.get(f"/api/audit-logs?incident_id={incident_id}&limit=50")
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) > 0
    for log in audit_logs:
        assert "policy_decision" in log
        assert "tool_called" in log
        assert "amount_paise" in log
