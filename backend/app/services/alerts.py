from app.repositories.alerts import list_alerts, resolve_alert
from app.schemas.alert import AlertSummary


def list_registered_alerts() -> list[AlertSummary]:
    return list_alerts()


def resolve_registered_alert(alert_id: int) -> bool:
    return resolve_alert(alert_id)
