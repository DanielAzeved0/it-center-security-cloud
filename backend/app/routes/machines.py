from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.machine import MachineDetail, MachineLocalAdmin, MachineMetric, MachineProgram, MachineSummary
from app.services.auth import CurrentUser, require_roles
from app.services.machines import (
    get_registered_machine,
    list_registered_machine_local_admins,
    list_registered_machine_metrics,
    list_registered_machine_programs,
    list_registered_machines,
)

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=list[MachineSummary])
def list_machines(
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineSummary]:
    return list_registered_machines()


@router.get("/{machine_id}", response_model=MachineDetail)
def get_machine(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> MachineDetail:
    machine = get_registered_machine(machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


@router.get("/{machine_id}/metrics", response_model=list[MachineMetric])
def list_machine_metrics(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineMetric]:
    metrics = list_registered_machine_metrics(machine_id)

    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return metrics


@router.get("/{machine_id}/programs", response_model=list[MachineProgram])
def list_machine_programs(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineProgram]:
    programs = list_registered_machine_programs(machine_id)

    if programs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return programs


@router.get("/{machine_id}/admins", response_model=list[MachineLocalAdmin])
def list_machine_local_admins(
    machine_id: int,
    current_user: CurrentUser = Depends(require_roles("admin", "analyst", "viewer")),
) -> list[MachineLocalAdmin]:
    admins = list_registered_machine_local_admins(machine_id)

    if admins is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return admins
