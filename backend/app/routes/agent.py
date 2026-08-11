from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.schemas.agent import AgentCheckinRequest, AgentCheckinResponse
from app.services.agent import process_agent_checkin

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/checkin", response_model=AgentCheckinResponse)
def checkin(
    payload: AgentCheckinRequest,
    x_agent_api_key: Annotated[str | None, Header(alias="X-Agent-Api-Key")] = None,
) -> AgentCheckinResponse:
    settings = get_settings()

    if not settings.agent_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent API key is not configured",
        )

    if not x_agent_api_key or not compare_digest(x_agent_api_key, settings.agent_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing agent API key",
        )

    return process_agent_checkin(payload)
