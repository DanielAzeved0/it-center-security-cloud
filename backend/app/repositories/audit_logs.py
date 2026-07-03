from psycopg.types.json import Jsonb

from app.database import get_connection


def create_audit_log(
    *,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                ip_address,
                user_agent,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                ip_address,
                user_agent,
                Jsonb(metadata or {}),
            ),
        )
