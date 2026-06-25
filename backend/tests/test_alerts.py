from fastapi.testclient import TestClient

from app.main import app


def test_list_alerts_returns_empty_list():
    client = TestClient(app)

    response = client.get("/api/v1/alerts")

    assert response.status_code == 200
    assert response.json() == []
