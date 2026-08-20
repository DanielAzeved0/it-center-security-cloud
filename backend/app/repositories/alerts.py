from app.database import get_connection
from app.schemas.alert import AlertSummary


def create_open_alert_once(
    *,
    machine_id: int,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO alerts (
                machine_id,
                alert_type,
                severity,
                status,
                title,
                description
            )
            VALUES (%s, %s, %s, 'open', %s, %s)
            ON CONFLICT (machine_id, alert_type) WHERE status IN ('open', 'investigating')
            DO NOTHING
            RETURNING id
            """,
            (
                machine_id,
                alert_type,
                severity,
                title,
                description,
            ),
        ).fetchone()

    return row is not None


def list_alerts(
    machine_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AlertSummary]:
    query = """
        SELECT
            id,
            machine_id,
            alert_type,
            severity,
            status,
            title,
            description,
            created_at
        FROM alerts
    """
    params: list[object] = []

    if machine_id is not None:
        query += " WHERE machine_id = %s"
        params.append(machine_id)

    query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [AlertSummary(**row) for row in rows]


def resolve_alert(alert_id: int) -> bool:
    with get_connection() as connection:
        row = connection.execute(
            """
            UPDATE alerts
            SET
                status = 'resolved',
                resolved_at = now()
            WHERE id = %s
            RETURNING id
            """,
            (alert_id,),
        ).fetchone()

    return row is not None
