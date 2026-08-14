from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from tests.test_agent_checkin import VALID_PAYLOAD


def test_list_machines_returns_empty_list_when_no_checkins(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_machines_returns_checked_in_machine(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machines_response = client.get("/api/v1/machines", headers=auth_headers)

    assert checkin_response.status_code == 200
    assert machines_response.status_code == 200

    machines = machines_response.json()
    assert len(machines) == 1
    assert machines[0]["id"] == checkin_response.json()["machine_id"]
    assert machines[0]["hostname"] == "PC-FINANCEIRO-01"
    assert machines[0]["username"] == "daniel"
    assert machines[0]["ip_address"] == "192.168.15.25"
    assert machines[0]["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert machines[0]["serial_number"] == "5M56TH4"
    assert machines[0]["status"] == "online"
    assert machines[0]["last_seen"]


def test_get_machine_returns_checked_in_machine_details(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}", headers=auth_headers)

    assert response.status_code == 200
    machine = response.json()
    assert machine["hostname"] == "PC-FINANCEIRO-01"
    assert machine["username"] == "daniel"
    assert machine["ip_address"] == "192.168.15.25"
    assert machine["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert machine["serial_number"] == "5M56TH4"
    assert machine["operating_system"] == "Windows 11 Pro"
    assert machine["os_version"] == "23H2"
    assert machine["status"] == "online"
    assert machine["last_seen"]


def test_get_machine_returns_404_when_not_found(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines/999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_list_machine_metrics_returns_checked_in_metrics(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}/metrics", headers=auth_headers)

    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics) == 1
    assert metrics[0]["cpu_usage"] == VALID_PAYLOAD["cpu_usage"]
    assert metrics[0]["ram_usage"] == VALID_PAYLOAD["ram_usage"]
    assert metrics[0]["disk_usage"] == VALID_PAYLOAD["disk_usage"]
    assert metrics[0]["uptime_seconds"] == VALID_PAYLOAD["uptime_seconds"]
    assert metrics[0]["created_at"]


def test_list_machine_metrics_returns_404_when_machine_not_found(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/metrics", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_list_machine_programs_returns_checked_in_programs(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}/programs", headers=auth_headers)

    assert response.status_code == 200
    programs = response.json()
    assert programs == VALID_PAYLOAD["installed_programs"]


def test_list_machine_programs_returns_404_when_machine_not_found(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/programs", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_list_machine_local_admins_returns_checked_in_admins(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    response = client.get(f"/api/v1/machines/{checkin_response.json()['machine_id']}/admins", headers=auth_headers)

    assert response.status_code == 200
    admins = response.json()
    assert [admin["admin_name"] for admin in admins] == ["Administrator", "Daniel"]
    assert all(admin["first_seen_at"] for admin in admins)
    assert all(admin["last_seen_at"] for admin in admins)


def test_list_machine_local_admins_returns_404_when_machine_not_found(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/admins", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_recent_machine_remains_online_and_does_not_create_offline_event(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    response = client.get("/api/v1/machines", headers=auth_headers)

    assert checkin_response.status_code == 200
    assert response.status_code == 200
    assert response.json()[0]["status"] == "online"

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'machine_offline'"
        ).fetchone()["count"]

    assert event_count == 0


def test_stale_machine_transitions_to_offline_and_registers_event(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machine_id = checkin_response.json()["machine_id"]

    with get_connection() as connection:
        connection.execute(
            "UPDATE machines SET last_seen = now() - interval '11 minutes' WHERE id = %s",
            (machine_id,),
        )

    response = client.get("/api/v1/machines", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()[0]["status"] == "offline"

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT machine_id, event_type, severity, source, description
            FROM security_events
            WHERE event_type = 'machine_offline'
            """
        ).fetchall()

    assert len(events) == 1
    assert events[0]["machine_id"] == machine_id
    assert events[0]["severity"] == "low"
    assert events[0]["source"] == "system"
    assert "mais de 10 minutos" in events[0]["description"]


def test_stale_machine_offline_event_is_not_duplicated_by_repeated_reads(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machine_id = checkin_response.json()["machine_id"]

    with get_connection() as connection:
        connection.execute(
            "UPDATE machines SET last_seen = now() - interval '11 minutes' WHERE id = %s",
            (machine_id,),
        )

    first_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)
    second_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["status"] == "offline"
    assert second_response.json()["status"] == "offline"

    with get_connection() as connection:
        event_count = connection.execute(
            "SELECT count(*) FROM security_events WHERE event_type = 'machine_offline'"
        ).fetchone()["count"]

    assert event_count == 1


def test_offline_machine_returns_online_after_new_checkin(monkeypatch, auth_headers):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machine_id = checkin_response.json()["machine_id"]

    with get_connection() as connection:
        connection.execute(
            "UPDATE machines SET last_seen = now() - interval '11 minutes' WHERE id = %s",
            (machine_id,),
        )

    offline_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)
    new_checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    online_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)

    assert offline_response.status_code == 200
    assert offline_response.json()["status"] == "offline"
    assert new_checkin_response.status_code == 200
    assert online_response.status_code == 200
    assert online_response.json()["status"] == "online"
