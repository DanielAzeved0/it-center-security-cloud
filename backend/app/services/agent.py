from app.schemas.agent import AgentCheckinRequest, AgentCheckinResponse
from app.repositories.machines import save_machine_checkin


def process_agent_checkin(payload: AgentCheckinRequest) -> AgentCheckinResponse:
    machine = save_machine_checkin(payload)

    return AgentCheckinResponse(
        status="success",
        message="Check-in received",
        machine_id=machine.id,
    )
