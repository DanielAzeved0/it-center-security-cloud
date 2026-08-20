from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


def _insert_machine(hostname: str) -> int:
    with get_connection() as connection:
        return connection.execute(
            "INSERT INTO machines (hostname, status) VALUES (%s, 'offline') RETURNING id",
            (hostname,),
        ).fetchone()["id"]


def _insert_security_event(machine_id: int, event_type: str = "usb_detected") -> int:
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO security_events (machine_id, event_type, severity, source, description)
            VALUES (%s, %s, 'low', 'agent', 'teste')
            RETURNING id
            """,
            (machine_id, event_type),
        ).fetchone()["id"]


def test_list_security_events_returns_empty_list(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/security-events", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_security_events_filters_by_machine_id(auth_headers):
    client = TestClient(app)
    machine_a = _insert_machine("PC-A")
    machine_b = _insert_machine("PC-B")
    _insert_security_event(machine_a)
    _insert_security_event(machine_b)

    response = client.get(f"/api/v1/security-events?machine_id={machine_a}", headers=auth_headers)

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["machine_id"] == machine_a


def test_list_security_events_respects_limit_and_offset(auth_headers):
    client = TestClient(app)
    machine_id = _insert_machine("PC-PAGINACAO")
    inserted_ids = [_insert_security_event(machine_id, event_type=f"type_{i}") for i in range(3)]

    first_page = client.get("/api/v1/security-events?limit=2&offset=0", headers=auth_headers)
    second_page = client.get("/api/v1/security-events?limit=2&offset=2", headers=auth_headers)

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert [event["id"] for event in first_page.json()] == list(reversed(inserted_ids))[:2]
    assert [event["id"] for event in second_page.json()] == list(reversed(inserted_ids))[2:]
