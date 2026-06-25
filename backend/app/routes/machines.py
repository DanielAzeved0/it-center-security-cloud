from fastapi import APIRouter

from app.schemas.machine import MachineSummary
from app.services.machines import list_registered_machines

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=list[MachineSummary])
def list_machines() -> list[MachineSummary]:
    return list_registered_machines()
