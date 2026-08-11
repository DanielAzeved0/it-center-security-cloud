from fastapi.testclient import TestClient

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


def test_executive_report_returns_pdf(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/reports/executive.pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "relatorio-executivo.pdf" in response.headers["content-disposition"]
    assert response.content[:4] == b"%PDF"


def test_executive_report_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/v1/reports/executive.pdf")

    assert response.status_code == 401


def test_viewer_can_read_executive_report():
    viewer_id = create_test_user(email="viewer@example.com", role="viewer")
    token, _ = create_access_token(user_id=viewer_id)
    client = TestClient(app)

    response = client.get(
        "/api/v1/reports/executive.pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


def test_machine_report_returns_pdf_for_existing_machine(monkeypatch, auth_headers):
    client = TestClient(app)
    machine_id = _checkin_machine(client, monkeypatch)

    response = client.get(f"/api/v1/machines/{machine_id}/report.pdf", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "relatorio-pc-financeiro-01.pdf" in response.headers["content-disposition"]
    assert response.content[:4] == b"%PDF"


def test_machine_report_returns_404_when_machine_not_found(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/machines/999/report.pdf", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Machine not found"}
