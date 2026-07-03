from fastapi.testclient import TestClient

from app.main import app


def test_list_security_events_returns_empty_list(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/security-events", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
