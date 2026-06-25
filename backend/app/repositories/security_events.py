from app.database import get_connection
from app.schemas.security_event import SecurityEventSummary


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
