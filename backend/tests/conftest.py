import pytest

from app.database import get_connection
from app.services.auth import create_access_token, hash_password


@pytest.fixture(autouse=True)
def clean_database():
    with get_connection() as connection:
        with connection.transaction():
            connection.execute(
                """
                TRUNCATE TABLE
                    audit_logs,
                    users,
                    machine_local_admins,
                    agent_configs,
                    alerts,
                    security_events,
                    installed_programs,
                    metrics,
                    machines
                RESTART IDENTITY CASCADE
                """
            )

    yield


def create_test_user(
    *,
    email: str = "admin@example.com",
    password: str = "StrongPass123!",
    role: str = "admin",
    status: str = "active",
) -> int:
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO users (email, name, password_hash, role, status)
            VALUES (%s, 'Test User', %s, %s, %s)
            RETURNING id
            """,
            (email, hash_password(password), role, status),
        ).fetchone()["id"]


@pytest.fixture
def auth_headers():
    user_id = create_test_user()
    token, _ = create_access_token(user_id=user_id)
    return {"Authorization": f"Bearer {token}"}
