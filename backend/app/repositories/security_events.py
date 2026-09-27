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


def create_security_events_batch(events: list[dict]) -> None:
    if not events:
        return

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO security_events (
                    machine_id,
                    event_type,
                    severity,
                    source,
                    description,
                    raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        e["machine_id"],
                        e["event_type"],
                        e["severity"],
                        e.get("source", "agent"),
                        e["description"],
                        Jsonb(e["raw_data"]) if e.get("raw_data") is not None else None,
                    )
                    for e in events
                ],
            )


def list_security_events(
    machine_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[SecurityEventSummary]:
    query = """
        SELECT
            id,
            machine_id,
            event_type,
            severity,
            source,
            description,
            created_at
        FROM security_events
    """
    params: list[object] = []

    if machine_id is not None:
        query += " WHERE machine_id = %s"
        params.append(machine_id)

    query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [SecurityEventSummary(**row) for row in rows]
