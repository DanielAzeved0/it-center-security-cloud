from fastapi.testclient import TestClient

from app.main import app
from app.services.auth import create_access_token
from tests.conftest import create_test_user


def test_logout_invalidates_token_immediately():
    user_id = create_test_user(email="user@example.com")
    token, _ = create_access_token(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    # 1. Access GET /api/v1/auth/me -> 200 OK
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == "user@example.com"

    # 2. Call POST /api/v1/auth/logout -> 200 OK
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json()["status"] == "success"

    # 3. Access GET /api/v1/auth/me again with same token -> 401 Unauthorized
    me_after_logout = client.get("/api/v1/auth/me", headers=headers)
    assert me_after_logout.status_code == 401
    assert me_after_logout.json() == {"detail": "Invalid or missing authentication token"}


def test_revoked_token_cannot_access_other_protected_endpoints():
    user_id = create_test_user(email="admin@example.com", role="admin")
    token, _ = create_access_token(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    # Logout to revoke
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    # Try accessing protected endpoint /api/v1/machines
    machines_response = client.get("/api/v1/machines", headers=headers)
    assert machines_response.status_code == 401
    assert machines_response.json() == {"detail": "Invalid or missing authentication token"}
