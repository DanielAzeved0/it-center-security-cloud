from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app


def test_list_alerts_returns_empty_list():
    client = TestClient(app)

    response = client.get("/api/v1/alerts")

    assert response.status_code == 200
    assert response.json() == []


def test_resolve_alert_marks_alert_as_resolved():
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

    response = client.patch(f"/api/v1/alerts/{alert_id}/resolve")

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


def test_resolve_alert_returns_404_when_not_found():
    client = TestClient(app)

    response = client.patch("/api/v1/alerts/999/resolve")

    assert response.status_code == 404
    assert response.json() == {"detail": "Alert not found"}
