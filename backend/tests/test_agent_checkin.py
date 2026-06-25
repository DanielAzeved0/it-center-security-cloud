from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


VALID_PAYLOAD = {
    "hostname": "PC-FINANCEIRO-01",
    "username": "daniel",
    "ip_address": "192.168.15.25",
    "operating_system": "Windows 11 Pro",
    "os_version": "23H2",
    "cpu_usage": 22.5,
    "ram_usage": 61.2,
    "disk_usage": 74.8,
    "uptime_seconds": 86400,
    "installed_programs": [
        {
            "name": "Google Chrome",
            "version": "126.0",
            "publisher": "Google",
        }
    ],
    "security": {
        "firewall_enabled": True,
        "defender_enabled": True,
        "rdp_enabled": False,
        "local_admins": ["Administrator", "Daniel"],
        "usb_devices": [],
        "failed_logins_last_hour": 0,
    },
}


def test_agent_checkin_accepts_valid_payload(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Check-in received",
        "machine_id": 1,
    }


def test_agent_checkin_persists_machine_metrics_and_programs(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200

    with get_connection() as connection:
        machine_count = connection.execute("SELECT count(*) FROM machines").fetchone()["count"]
        metric_count = connection.execute("SELECT count(*) FROM metrics").fetchone()["count"]
        program_count = connection.execute("SELECT count(*) FROM installed_programs").fetchone()["count"]

    assert machine_count == 1
    assert metric_count == 1
    assert program_count == 1


def test_agent_checkin_rejects_missing_api_key(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post("/api/v1/agent/checkin", json=VALID_PAYLOAD)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing agent API key"}


def test_agent_checkin_rejects_invalid_payload(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)
    payload = {**VALID_PAYLOAD, "cpu_usage": 101}

    response = client.post(
        "/api/v1/agent/checkin",
        json=payload,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 422
