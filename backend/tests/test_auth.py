from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.auth import create_access_token
from tests.conftest import create_test_user


def test_login_returns_token_for_active_user():
    create_test_user(email="admin@example.com", password="StrongPass123!", role="admin", status="active")
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] > 0
    assert payload["user"] == {
        "id": 1,
        "email": "admin@example.com",
        "name": "Test User",
        "role": "admin",
    }

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT actor_user_id, action, entity_type FROM audit_logs WHERE action = 'auth.login'"
        ).fetchone()

    assert audit_log == {
        "actor_user_id": 1,
        "action": "auth.login",
        "entity_type": "user",
    }


def test_login_rejects_invalid_password_with_generic_error():
    create_test_user(email="admin@example.com", password="StrongPass123!")
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT actor_user_id, action, entity_type FROM audit_logs WHERE action = 'auth.login_failed'"
        ).fetchone()

    assert audit_log == {
        "actor_user_id": None,
        "action": "auth.login_failed",
        "entity_type": "auth",
    }


def test_login_rejects_disabled_and_pending_users():
    create_test_user(email="disabled@example.com", password="StrongPass123!", status="disabled")
    create_test_user(email="pending@example.com", password="StrongPass123!", status="pending")
    client = TestClient(app)

    disabled_response = client.post(
        "/api/v1/auth/login",
        json={"email": "disabled@example.com", "password": "StrongPass123!"},
    )
    pending_response = client.post(
        "/api/v1/auth/login",
        json={"email": "pending@example.com", "password": "StrongPass123!"},
    )

    assert disabled_response.status_code == 401
    assert pending_response.status_code == 401


def test_me_returns_current_user(auth_headers):
    client = TestClient(app)

    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "admin@example.com"


def test_logout_records_audit_log(auth_headers):
    client = TestClient(app)

    response = client.post("/api/v1/auth/logout", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Logged out"}

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT actor_user_id, action, entity_type FROM audit_logs WHERE action = 'auth.logout'"
        ).fetchone()

    assert audit_log["actor_user_id"] == 1
    assert audit_log["entity_type"] == "user"


def test_admin_route_requires_token():
    client = TestClient(app)

    response = client.get("/api/v1/machines")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing authentication token"}


def test_admin_route_rejects_invalid_token():
    client = TestClient(app)

    response = client.get("/api/v1/machines", headers={"Authorization": "Bearer invalid"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing authentication token"}


def test_admin_route_rejects_expired_token():
    user_id = create_test_user()
    token, _ = create_access_token(user_id=user_id, expires_in_seconds=-1)
    client = TestClient(app)

    response = client.get("/api/v1/machines", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
