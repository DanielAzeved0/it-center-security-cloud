from app.repositories.machines import list_machines
from app.schemas.machine import MachineSummary


def list_registered_machines() -> list[MachineSummary]:
    return list_machines()
