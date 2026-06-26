from app.database import get_connection
from app.schemas.security_event import SecurityEventSummary
from psycopg.types.json import Jsonb


def create_security_event(
    *,
    machine_id: int,
    event_type: str,
    severity: str,
    description: str,
    raw_data: dict,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO security_events (
                machine_id,
                event_type,
                severity,
                source,
                description,
                raw_data
            )
            VALUES (%s, %s, %s, 'agent', %s, %s)
            """,
            (
                machine_id,
                event_type,
                severity,
                description,
                Jsonb(raw_data),
            ),
        )


def list_security_events() -> list[SecurityEventSummary]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                machine_id,
                event_type,
                severity,
                source,
                description,
                created_at
            FROM security_events
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

    return [SecurityEventSummary(**row) for row in rows]
