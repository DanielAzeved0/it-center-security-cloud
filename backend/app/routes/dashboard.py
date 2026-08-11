from fastapi import APIRouter, Depends

from app.schemas.dashboard import DashboardSummary
from app.services.auth import CurrentUser, require_roles
from app.services.dashboard import get_registered_dashboard_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary_view(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> DashboardSummary:
    return get_registered_dashboard_summary()
