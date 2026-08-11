from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.auth import create_access_token
from tests.conftest import create_test_user


def _insert_machine(hostname: str, status: str) -> int:
    last_seen_expression = "now()" if status == "online" else "NULL"

    with get_connection() as connection:
        return connection.execute(
            f"""
            INSERT INTO machines (hostname, status, last_seen)
            VALUES (%s, %s, {last_seen_expression})
            RETURNING id
            """,
            (hostname, status),
        ).fetchone()["id"]


def _insert_alert(*, machine_id: int, severity: str, status: str) -> None:
    resolved_at_expression = "now()" if status in ("resolved", "ignored") else "NULL"

    with get_connection() as connection:
        connection.execute(
            f"""
            INSERT INTO alerts (machine_id, alert_type, severity, status, title, description, resolved_at)
            VALUES (%s, 'unauthorized_remote_access_tool', %s, %s, 'Alerta de teste', 'Descricao de teste', {resolved_at_expression})
            """,
            (machine_id, severity, status),
        )


def _insert_security_event(*, machine_id: int, severity: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO security_events (machine_id, event_type, severity, source, description, raw_data)
            VALUES (%s, 'usb_device_connected', %s, 'agent', 'Evento de teste', '{}')
            """,
            (machine_id, severity),
        )


def test_dashboard_summary_returns_zero_counts_when_empty(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "machines_total": 0,
        "machines_online": 0,
        "machines_offline": 0,
        "alerts_open_total": 0,
        "alerts_open_by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        "recent_events": [],
    }


def test_dashboard_summary_counts_machines_and_open_alerts_by_severity(auth_headers):
    client = TestClient(app)

    online_id = _insert_machine("PC-ONLINE-01", "online")
    offline_id = _insert_machine("PC-OFFLINE-01", "offline")

    _insert_alert(machine_id=online_id, severity="high", status="open")
    _insert_alert(machine_id=online_id, severity="high", status="investigating")
    _insert_alert(machine_id=offline_id, severity="low", status="resolved")
    _insert_security_event(machine_id=online_id, severity="medium")

    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()

    assert payload["machines_total"] == 2
    assert payload["machines_online"] == 1
    assert payload["machines_offline"] == 1
    assert payload["alerts_open_total"] == 2
    assert payload["alerts_open_by_severity"] == {"low": 0, "medium": 0, "high": 2, "critical": 0}
    assert len(payload["recent_events"]) == 1
    assert payload["recent_events"][0]["event_type"] == "usb_device_connected"


def test_dashboard_summary_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 401


def test_viewer_can_read_dashboard_summary():
    viewer_id = create_test_user(email="viewer@example.com", role="viewer")
    token, _ = create_access_token(user_id=viewer_id)
    client = TestClient(app)

    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
