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
        with connection.transaction():
            existing = connection.execute(
                """
                SELECT id
                FROM alerts
                WHERE
                    machine_id = %s
                    AND alert_type = %s
                    AND status IN ('open', 'investigating')
                LIMIT 1
                """,
                (machine_id, alert_type),
            ).fetchone()

            if existing is not None:
                return False

            connection.execute(
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
                """,
                (
                    machine_id,
                    alert_type,
                    severity,
                    title,
                    description,
                ),
            )

    return True


def list_alerts() -> list[AlertSummary]:
    with get_connection() as connection:
        rows = connection.execute(
            """
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
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

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
