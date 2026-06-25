from fastapi.testclient import TestClient

from app.main import app
from tests.test_agent_checkin import VALID_PAYLOAD


def test_list_machines_returns_empty_list_when_no_checkins():
    client = TestClient(app)

    response = client.get("/api/v1/machines")

    assert response.status_code == 200
    assert response.json() == []


def test_list_machines_returns_checked_in_machine(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machines_response = client.get("/api/v1/machines")

    assert checkin_response.status_code == 200
    assert machines_response.status_code == 200

    machines = machines_response.json()
    assert len(machines) == 1
    assert machines[0]["id"] == checkin_response.json()["machine_id"]
    assert machines[0]["hostname"] == "PC-FINANCEIRO-01"
    assert machines[0]["username"] == "daniel"
    assert machines[0]["ip_address"] == "192.168.15.25"
    assert machines[0]["status"] == "online"
    assert machines[0]["last_seen"]
