import pytest
from psycopg import errors

from app.database import get_connection


def insert_user(
    *,
    email: str = "admin@example.com",
    name: str = "Admin User",
    password_hash: str = "hash-value",
    role: str = "admin",
    status: str = "active",
) -> dict:
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO users (email, name, password_hash, role, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING
                id,
                email,
                name,
                password_hash,
                role,
                status,
                created_at,
                updated_at,
                last_login_at
            """,
            (email, name, password_hash, role, status),
        ).fetchone()


def test_users_table_accepts_valid_admin_user():
    user = insert_user()

    assert user["id"] == 1
    assert user["email"] == "admin@example.com"
    assert user["name"] == "Admin User"
    assert user["password_hash"] == "hash-value"
    assert user["role"] == "admin"
    assert user["status"] == "active"
    assert user["created_at"] is not None
    assert user["updated_at"] is not None
    assert user["last_login_at"] is None


@pytest.mark.parametrize(
    ("role", "status"),
    [
        ("admin", "active"),
        ("analyst", "pending"),
        ("viewer", "disabled"),
    ],
)
def test_users_table_accepts_allowed_roles_and_statuses(role, status):
    user = insert_user(
        email=f"{role}-{status}@example.com",
        role=role,
        status=status,
    )

    assert user["role"] == role
    assert user["status"] == status


def test_users_table_rejects_duplicate_email_case_insensitive():
    insert_user(email="Admin@Example.com")

    with pytest.raises(errors.UniqueViolation):
        insert_user(email="admin@example.com")


@pytest.mark.parametrize(
    "field",
    [
        "email",
        "name",
        "password_hash",
        "role",
        "status",
    ],
)
def test_users_table_rejects_required_null_fields(field):
    values = {
        "email": "admin@example.com",
        "name": "Admin User",
        "password_hash": "hash-value",
        "role": "admin",
        "status": "active",
    }
    values[field] = None

    with pytest.raises(errors.NotNullViolation):
        insert_user(**values)


@pytest.mark.parametrize(
    "field",
    [
        "email",
        "name",
        "password_hash",
    ],
)
def test_users_table_rejects_blank_text_fields(field):
    values = {
        "email": "admin@example.com",
        "name": "Admin User",
        "password_hash": "hash-value",
        "role": "admin",
        "status": "active",
    }
    values[field] = " "

    with pytest.raises(errors.CheckViolation):
        insert_user(**values)


def test_users_table_rejects_invalid_role():
    with pytest.raises(errors.CheckViolation):
        insert_user(role="operator")


def test_users_table_rejects_invalid_status():
    with pytest.raises(errors.CheckViolation):
        insert_user(status="locked")
