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


def test_get_machine_returns_checked_in_machine_details(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}")

    assert response.status_code == 200
    machine = response.json()
    assert machine["hostname"] == "PC-FINANCEIRO-01"
    assert machine["username"] == "daniel"
    assert machine["ip_address"] == "192.168.15.25"
    assert machine["operating_system"] == "Windows 11 Pro"
    assert machine["os_version"] == "23H2"
    assert machine["status"] == "online"
    assert machine["last_seen"]


def test_get_machine_returns_404_when_not_found():
    client = TestClient(app)

    response = client.get("/api/v1/machines/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_list_machine_metrics_returns_checked_in_metrics(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}/metrics")

    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) == 1
    assert metrics[0]["cpu_usage"] == VALID_PAYLOAD["cpu_usage"]
    assert metrics[0]["ram_usage"] == VALID_PAYLOAD["ram_usage"]
    assert metrics[0]["disk_usage"] == VALID_PAYLOAD["disk_usage"]
    assert metrics[0]["uptime_seconds"] == VALID_PAYLOAD["uptime_seconds"]
    assert metrics[0]["created_at"]


def test_list_machine_metrics_returns_404_when_machine_not_found():
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/metrics")

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_list_machine_programs_returns_checked_in_programs(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}/programs")

    assert response.status_code == 200
    programs = response.json()
    assert programs == VALID_PAYLOAD["installed_programs"]


def test_list_machine_programs_returns_404_when_machine_not_found():
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/programs")

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}
