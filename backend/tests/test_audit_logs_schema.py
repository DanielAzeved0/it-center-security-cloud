import pytest
from psycopg import errors
from psycopg.types.json import Jsonb

from app.database import get_connection


def insert_user(email: str = "admin@example.com") -> int:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO users (email, name, password_hash, role, status)
            VALUES (%s, 'Admin User', 'hash-value', 'admin', 'active')
            RETURNING id
            """,
            (email,),
        ).fetchone()

    return row["id"]


def insert_audit_log(
    *,
    actor_user_id: int | None = None,
    action: str | None = "alert.resolve",
    entity_type: str | None = "alert",
    entity_id: str | None = "1",
    ip_address: str | None = "192.168.15.10",
    user_agent: str | None = "pytest",
    metadata: dict | None = None,
) -> dict:
    fields = [
        "actor_user_id",
        "action",
        "entity_type",
        "entity_id",
        "ip_address",
        "user_agent",
    ]
    values = [
        actor_user_id,
        action,
        entity_type,
        entity_id,
        ip_address,
        user_agent,
    ]

    if metadata is not None:
        fields.append("metadata")
        values.append(Jsonb(metadata))

    placeholders = ", ".join(["%s"] * len(values))

    with get_connection() as connection:
        return connection.execute(
            f"""
            INSERT INTO audit_logs ({", ".join(fields)})
            VALUES ({placeholders})
            RETURNING
                id,
                actor_user_id,
                action,
                entity_type,
                entity_id,
                host(ip_address) AS ip_address,
                user_agent,
                metadata,
                created_at
            """,
            values,
        ).fetchone()


def test_audit_logs_table_accepts_user_actor():
    user_id = insert_user()

    audit_log = insert_audit_log(
        actor_user_id=user_id,
        metadata={"status": "resolved"},
    )

    assert audit_log["id"] == 1
    assert audit_log["actor_user_id"] == user_id
    assert audit_log["action"] == "alert.resolve"
    assert audit_log["entity_type"] == "alert"
    assert audit_log["entity_id"] == "1"
    assert audit_log["ip_address"] == "192.168.15.10"
    assert audit_log["user_agent"] == "pytest"
    assert audit_log["metadata"] == {"status": "resolved"}
    assert audit_log["created_at"] is not None


def test_audit_logs_table_accepts_system_event_without_actor():
    audit_log = insert_audit_log(
        actor_user_id=None,
        action="system.job",
        entity_type="system",
        entity_id=None,
        ip_address=None,
        user_agent=None,
    )

    assert audit_log["actor_user_id"] is None
    assert audit_log["entity_id"] is None
    assert audit_log["ip_address"] is None
    assert audit_log["user_agent"] is None


def test_audit_logs_table_defaults_metadata_to_empty_object():
    audit_log = insert_audit_log()

    assert audit_log["metadata"] == {}


@pytest.mark.parametrize("field", ["action", "entity_type"])
def test_audit_logs_table_rejects_required_null_fields(field):
    values = {
        "action": "alert.resolve",
        "entity_type": "alert",
    }
    values[field] = None

    with pytest.raises(errors.NotNullViolation):
        insert_audit_log(**values)


@pytest.mark.parametrize("field", ["action", "entity_type"])
def test_audit_logs_table_rejects_blank_text_fields(field):
    values = {
        "action": "alert.resolve",
        "entity_type": "alert",
    }
    values[field] = " "

    with pytest.raises(errors.CheckViolation):
        insert_audit_log(**values)


def test_audit_logs_table_rejects_unknown_actor_user_id():
    with pytest.raises(errors.ForeignKeyViolation):
        insert_audit_log(actor_user_id=999)


def test_audit_logs_table_clears_actor_when_user_is_deleted():
    user_id = insert_user()
    audit_log = insert_audit_log(actor_user_id=user_id)

    with get_connection() as connection:
        connection.execute("DELETE FROM users WHERE id = %s", (user_id,))
        stored_audit_log = connection.execute(
            "SELECT actor_user_id FROM audit_logs WHERE id = %s",
            (audit_log["id"],),
        ).fetchone()

    assert stored_audit_log["actor_user_id"] is None
