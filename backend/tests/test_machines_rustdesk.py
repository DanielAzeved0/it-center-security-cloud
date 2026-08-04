from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.auth import create_access_token
from tests.conftest import create_test_user
from tests.test_agent_checkin import VALID_PAYLOAD


def _checkin_machine(client: TestClient, monkeypatch) -> int:
    monkeypatch.setenv("AGENT_API_KEY", "test-key")

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )

    return checkin_response.json()["machine_id"]


def test_admin_can_update_rustdesk_id_and_it_persists(monkeypatch, auth_headers):
    client = TestClient(app)
    machine_id = _checkin_machine(client, monkeypatch)

    response = client.patch(
        f"/api/v1/machines/{machine_id}/rustdesk",
        json={"rustdesk_id": "123456789"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Rustdesk ID updated",
    }

    get_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)

    assert get_response.status_code == 200
    assert get_response.json()["rustdesk_id"] == "123456789"

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT action, entity_type, entity_id, metadata FROM audit_logs WHERE action = 'machine.rustdesk_update'"
        ).fetchone()

    assert audit_log["action"] == "machine.rustdesk_update"
    assert audit_log["entity_type"] == "machine"
    assert audit_log["entity_id"] == str(machine_id)
    assert audit_log["metadata"] == {"rustdesk_id": "123456789"}


def test_analyst_can_update_rustdesk_id(monkeypatch):
    client = TestClient(app)
    machine_id = _checkin_machine(client, monkeypatch)

    analyst_id = create_test_user(email="analyst@example.com", role="analyst")
    token, _ = create_access_token(user_id=analyst_id)

    response = client.patch(
        f"/api/v1/machines/{machine_id}/rustdesk",
        json={"rustdesk_id": "987654321"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Rustdesk ID updated",
    }


def test_viewer_cannot_update_rustdesk_id(monkeypatch):
    client = TestClient(app)
    machine_id = _checkin_machine(client, monkeypatch)

    viewer_id = create_test_user(email="viewer@example.com", role="viewer")
    token, _ = create_access_token(user_id=viewer_id)

    response = client.patch(
        f"/api/v1/machines/{machine_id}/rustdesk",
        json={"rustdesk_id": "123456789"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_update_rustdesk_id_returns_404_when_machine_not_found(auth_headers):
    client = TestClient(app)

    response = client.patch(
        "/api/v1/machines/999/rustdesk",
        json={"rustdesk_id": "123456789"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}


def test_admin_can_clear_rustdesk_id_with_null(monkeypatch, auth_headers):
    client = TestClient(app)
    machine_id = _checkin_machine(client, monkeypatch)

    client.patch(
        f"/api/v1/machines/{machine_id}/rustdesk",
        json={"rustdesk_id": "123456789"},
        headers=auth_headers,
    )

    response = client.patch(
        f"/api/v1/machines/{machine_id}/rustdesk",
        json={"rustdesk_id": None},
        headers=auth_headers,
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/v1/machines/{machine_id}", headers=auth_headers)

    assert get_response.json()["rustdesk_id"] is None
