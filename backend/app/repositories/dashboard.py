from app.database import get_connection
from app.repositories.machines import mark_stale_machines_offline
from app.schemas.dashboard import AlertSeverityCounts, DashboardSummary
from app.schemas.security_event import SecurityEventSummary

RECENT_EVENTS_LIMIT = 10


def get_dashboard_summary() -> DashboardSummary:
    mark_stale_machines_offline()

    with get_connection() as connection:
        machines_row = connection.execute(
            """
            SELECT
                count(*) AS total,
                count(*) FILTER (WHERE status = 'online') AS online,
                count(*) FILTER (WHERE status = 'offline') AS offline
            FROM machines
            """
        ).fetchone()

        severity_rows = connection.execute(
            """
            SELECT severity, count(*) AS total
            FROM alerts
            WHERE status IN ('open', 'investigating')
            GROUP BY severity
            """
        ).fetchall()

        event_rows = connection.execute(
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
            LIMIT %s
            """,
            (RECENT_EVENTS_LIMIT,),
        ).fetchall()

    severity_counts = AlertSeverityCounts(**{row["severity"]: row["total"] for row in severity_rows})

    return DashboardSummary(
        machines_total=machines_row["total"],
        machines_online=machines_row["online"],
        machines_offline=machines_row["offline"],
        alerts_open_total=sum(row["total"] for row in severity_rows),
        alerts_open_by_severity=severity_counts,
        recent_events=[SecurityEventSummary(**row) for row in event_rows],
    )
