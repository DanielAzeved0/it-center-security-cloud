from app.repositories.dashboard import get_dashboard_summary
from app.schemas.dashboard import DashboardSummary


def get_registered_dashboard_summary() -> DashboardSummary:
    return get_dashboard_summary()
