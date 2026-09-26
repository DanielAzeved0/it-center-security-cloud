import pytest
from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from app.services.risk_engine import get_risk_engine
from tests.conftest import create_test_user


@pytest.fixture(autouse=True)
def reset_engine():
    get_risk_engine().clear()
    yield
    get_risk_engine().clear()


def test_consecutive_failed_logins_trigger_429_with_retry_after():
    create_test_user(email="target@example.com", password="CorrectPassword123!")
    client = TestClient(app)
    headers = {"User-Agent": "AttackerBrowser/1.0", "Accept-Language": "en-US"}

    # 4 failed attempts in rapid succession (< 10 seconds):
    # Attempt 1: failure (20) -> 401
    # Attempt 2: failure (40) -> 401
    # Attempt 3: failure (60) -> 401
    # Attempt 4: failure (80) + burst (>3 in 10s = +35) = 115 >= 100 -> blocks client -> 401
    for attempt in range(1, 5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "target@example.com", "password": "wrong-password"},
            headers=headers,
        )
        assert resp.status_code == 401, f"Attempt {attempt} should return 401"
        assert resp.json() == {"detail": "Invalid credentials"}

    # 5th attempt: client is blocked prior to authentication -> 429
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "target@example.com", "password": "even-with-correct-password-should-block"},
        headers=headers,
    )
    assert resp.status_code == 429
    assert resp.json() == {"detail": "Too many attempts. Account locked temporarily."}
    assert "Retry-After" in resp.headers
    retry_after = int(resp.headers["Retry-After"])
    assert retry_after > 0
    assert retry_after <= 900

    # Verify audit log recorded auth.login_blocked_risk
    with get_connection() as connection:
        audit_log = connection.execute(
            """
            SELECT action, entity_type, metadata
            FROM audit_logs
            WHERE action = 'auth.login_blocked_risk'
            ORDER BY created_at DESC LIMIT 1
            """
        ).fetchone()

    assert audit_log is not None
    assert audit_log["action"] == "auth.login_blocked_risk"
    assert audit_log["entity_type"] == "auth"
    assert audit_log["metadata"]["email"] == "target@example.com"
    assert audit_log["metadata"]["risk_score"] >= 100
    assert audit_log["metadata"]["retry_after"] > 0


def test_successful_login_resets_risk_score():
    create_test_user(email="user@example.com", password="ValidPassword123!")
    client = TestClient(app)
    headers = {"User-Agent": "NormalBrowser/1.0", "Accept-Language": "pt-BR"}

    # 2 failed attempts
    for _ in range(2):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "bad-password"},
            headers=headers,
        )
        assert resp.status_code == 401

    # 1 successful login
    resp_success = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "ValidPassword123!"},
        headers=headers,
    )
    assert resp_success.status_code == 200

    # Subsequent failed attempts should start counting from 0 again
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "bad-password"},
        headers=headers,
    )
    assert resp.status_code == 401


def test_different_clients_isolated():
    create_test_user(email="user@example.com", password="ValidPassword123!")
    client = TestClient(app)

    headers_attacker = {"User-Agent": "AttackerBot/1.0", "Accept-Language": "en-US"}
    headers_legit = {"User-Agent": "LegitUser/1.0", "Accept-Language": "pt-BR"}

    # Attacker triggers block
    for _ in range(4):
        client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong"},
            headers=headers_attacker,
        )

    # Attacker is blocked
    resp_attacker = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong"},
        headers=headers_attacker,
    )
    assert resp_attacker.status_code == 429

    # Legit client is NOT blocked and can login successfully
    resp_legit = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "ValidPassword123!"},
        headers=headers_legit,
    )
    assert resp_legit.status_code == 200
