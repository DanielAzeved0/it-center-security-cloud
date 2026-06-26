from fastapi import APIRouter, HTTPException, status

from app.schemas.machine import MachineDetail, MachineMetric, MachineProgram, MachineSummary
from app.services.machines import (
    get_registered_machine,
    list_registered_machine_metrics,
    list_registered_machine_programs,
    list_registered_machines,
)

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


@router.get("", response_model=list[MachineSummary])
def list_machines() -> list[MachineSummary]:
    return list_registered_machines()


@router.get("/{machine_id}", response_model=MachineDetail)
def get_machine(machine_id: int) -> MachineDetail:
    machine = get_registered_machine(machine_id)

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return machine


@router.get("/{machine_id}/metrics", response_model=list[MachineMetric])
def list_machine_metrics(machine_id: int) -> list[MachineMetric]:
    metrics = list_registered_machine_metrics(machine_id)

    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return metrics


@router.get("/{machine_id}/programs", response_model=list[MachineProgram])
def list_machine_programs(machine_id: int) -> list[MachineProgram]:
    programs = list_registered_machine_programs(machine_id)

    if programs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found",
        )

    return programs
