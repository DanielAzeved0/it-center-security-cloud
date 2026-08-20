from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.repositories.alerts import create_open_alert_once


def _insert_machine(hostname: str) -> int:
    with get_connection() as connection:
        return connection.execute(
            "INSERT INTO machines (hostname, status) VALUES (%s, 'offline') RETURNING id",
            (hostname,),
        ).fetchone()["id"]


def _insert_alert(machine_id: int, alert_type: str = "torrent_software_detected") -> int:
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO alerts (machine_id, alert_type, severity, status, title, description)
            VALUES (%s, %s, 'high', 'open', 'Torrent detectado', 'qBittorrent encontrado')
            RETURNING id
            """,
            (machine_id, alert_type),
        ).fetchone()["id"]


def test_create_open_alert_once_is_idempotent(auth_headers):
    machine_id = _insert_machine("PC-IDEMPOTENTE-01")

    first = create_open_alert_once(
        machine_id=machine_id,
        alert_type="firewall_disabled",
        severity="high",
        title="Firewall desativado",
        description="teste",
    )
    second = create_open_alert_once(
        machine_id=machine_id,
        alert_type="firewall_disabled",
        severity="high",
        title="Firewall desativado",
        description="teste",
    )

    assert first is True
    assert second is False

    with get_connection() as connection:
        count = connection.execute(
            "SELECT count(*) FROM alerts WHERE machine_id = %s AND alert_type = 'firewall_disabled'",
            (machine_id,),
        ).fetchone()["count"]

    assert count == 1


def test_list_alerts_filters_by_machine_id(auth_headers):
    client = TestClient(app)
    machine_a = _insert_machine("PC-A")
    machine_b = _insert_machine("PC-B")
    _insert_alert(machine_a)
    _insert_alert(machine_b)

    response = client.get(f"/api/v1/alerts?machine_id={machine_a}", headers=auth_headers)

    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    assert alerts[0]["machine_id"] == machine_a


def test_list_alerts_respects_limit_and_offset(auth_headers):
    client = TestClient(app)
    machine_id = _insert_machine("PC-PAGINACAO")
    inserted_ids = [_insert_alert(machine_id, alert_type=f"type_{i}") for i in range(3)]

    first_page = client.get(f"/api/v1/alerts?limit=2&offset=0", headers=auth_headers)
    second_page = client.get(f"/api/v1/alerts?limit=2&offset=2", headers=auth_headers)

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert [alert["id"] for alert in first_page.json()] == list(reversed(inserted_ids))[:2]
    assert [alert["id"] for alert in second_page.json()] == list(reversed(inserted_ids))[2:]


def test_list_alerts_rejects_out_of_range_limit(auth_headers):
    client = TestClient(app)

    too_low = client.get("/api/v1/alerts?limit=0", headers=auth_headers)
    too_high = client.get("/api/v1/alerts?limit=501", headers=auth_headers)

    assert too_low.status_code == 422
    assert too_high.status_code == 422


def test_list_alerts_returns_empty_list(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/alerts", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_resolve_alert_marks_alert_as_resolved(auth_headers):
    client = TestClient(app)

    with get_connection() as connection:
        alert_id = connection.execute(
            """
            INSERT INTO alerts (
                alert_type,
                severity,
                status,
                title,
                description
            )
            VALUES (
                'torrent_software_detected',
                'high',
                'open',
                'Torrent detectado',
                'qBittorrent foi encontrado na maquina'
            )
            RETURNING id
            """
        ).fetchone()["id"]

    response = client.patch(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Alert resolved",
    }

    with get_connection() as connection:
        alert = connection.execute(
            "SELECT status, resolved_at FROM alerts WHERE id = %s",
            (alert_id,),
        ).fetchone()

    assert alert["status"] == "resolved"
    assert alert["resolved_at"] is not None

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT action, entity_type, entity_id FROM audit_logs WHERE action = 'alert.resolve'"
        ).fetchone()

    assert audit_log == {
        "action": "alert.resolve",
        "entity_type": "alert",
        "entity_id": str(alert_id),
    }


def test_resolve_alert_returns_404_when_not_found(auth_headers):
    client = TestClient(app)

    response = client.patch("/api/v1/alerts/999/resolve", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Alert not found"}


def test_viewer_cannot_resolve_alert():
    from app.services.auth import create_access_token
    from tests.conftest import create_test_user

    user_id = create_test_user(email="viewer@example.com", role="viewer")
    token, _ = create_access_token(user_id=user_id)
    client = TestClient(app)

    response = client.patch(
        "/api/v1/alerts/999/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}
