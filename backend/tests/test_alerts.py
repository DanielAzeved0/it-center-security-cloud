from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


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
