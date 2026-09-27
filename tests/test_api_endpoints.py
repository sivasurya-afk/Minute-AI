"""
Unit tests for Minute AI FastAPI backend routes.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "charts" in data
    assert "recent_transcripts" in data
    assert data["metrics"]["total_transcripts"] >= 0


def test_projects_crud():
    # List projects
    res = client.get("/api/projects")
    assert res.status_code == 200
    assert "projects" in res.json()

    # Create project
    create_res = client.post("/api/projects", json={
        "project_name": "API Gateway Squad",
        "project_key": "GATE",
        "description": "Gateway routing and edge rate limiting",
        "team_name": "Networking",
        "keywords": ["gateway", "proxy", "envoy"],
        "is_active": True,
    })
    assert create_res.status_code == 200
    proj = create_res.json()["project"]
    assert proj["project_key"] == "GATE"

    # Toggle active
    toggle_res = client.patch(f"/api/projects/{proj['id']}/toggle?is_active=false")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["project"]["is_active"] is False

    # Clean up delete
    del_res = client.delete(f"/api/projects/{proj['id']}")
    assert del_res.status_code == 200


def test_action_items_filtering_and_status():
    res = client.get("/api/action-items")
    assert res.status_code == 200
    data = res.json()
    assert "action_items" in data
    assert data["count"] >= 0

    if data["action_items"]:
        first_id = data["action_items"][0]["id"]
        # Update status
        st_res = client.patch(f"/api/action-items/{first_id}/status", json={"status": "Approved"})
        assert st_res.status_code == 200
        assert st_res.json()["action_item"]["status"] == "Approved"


def test_settings_endpoint():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert "groq_model" in data
    assert "confidence_threshold" in data
    assert "diagnostics" in data


def test_export_endpoints():
    csv_res = client.get("/api/export/csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")

    excel_res = client.get("/api/export/excel")
    assert excel_res.status_code == 200
    assert "spreadsheetml" in excel_res.headers["content-type"]
