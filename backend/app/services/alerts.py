from app.repositories.alerts import list_alerts, resolve_alert
from app.schemas.alert import AlertSummary


def list_registered_alerts(
    machine_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AlertSummary]:
    return list_alerts(machine_id=machine_id, limit=limit, offset=offset)


def resolve_registered_alert(alert_id: int) -> bool:
    return resolve_alert(alert_id)
