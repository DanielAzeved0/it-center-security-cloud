from fastapi.testclient import TestClient

import app.routes.auth as auth_route_module
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


def test_login_runs_password_verification_even_when_user_does_not_exist(monkeypatch):
    """EPIC 28: verify_password deve sempre rodar (contra o hash dummy
    pre-computado) mesmo quando o e-mail nao esta cadastrado, para nao
    revelar por timing quais e-mails existem."""
    original_verify_password = auth_route_module.verify_password
    calls: list[str] = []

    def spy_verify_password(password: str, password_hash: str) -> bool:
        calls.append(password_hash)
        return original_verify_password(password, password_hash)

    monkeypatch.setattr(auth_route_module, "verify_password", spy_verify_password)
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )

    assert response.status_code == 401
    assert calls == [auth_route_module._DUMMY_PASSWORD_HASH]


def test_login_records_x_real_ip_ignoring_forged_x_forwarded_for():
    """EPIC 28: audit_logs deve gravar X-Real-IP (nao forjavel pelo cliente
    atras do Nginx), nao o primeiro valor de X-Forwarded-For (anexavel)."""
    create_test_user(email="admin@example.com", password="StrongPass123!")
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
        headers={
            "X-Real-IP": "203.0.113.9",
            "X-Forwarded-For": "198.51.100.1, 203.0.113.9",
        },
    )

    assert response.status_code == 401

    with get_connection() as connection:
        audit_log = connection.execute(
            "SELECT host(ip_address) AS ip_address FROM audit_logs WHERE action = 'auth.login_failed'"
        ).fetchone()

    assert audit_log["ip_address"] == "203.0.113.9"


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
