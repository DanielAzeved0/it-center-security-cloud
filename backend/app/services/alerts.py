from app.repositories.alerts import list_alerts
from app.schemas.alert import AlertSummary


def list_registered_alerts() -> list[AlertSummary]:
    return list_alerts()
