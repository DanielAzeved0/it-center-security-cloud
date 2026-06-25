from app.database import get_connection
from app.schemas.alert import AlertSummary


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
