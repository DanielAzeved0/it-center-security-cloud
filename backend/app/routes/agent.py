from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Query, Response, status

from app.core.config import Settings, get_settings
from app.repositories.machines import get_machine_target_agent_version_by_hostname
from app.schemas.agent import AgentCheckinRequest, AgentCheckinResponse, AgentManifestResponse
from app.services.agent import process_agent_checkin
from app.services.agent_release import AgentReleaseNotConfigured, get_agent_release_bytes, get_agent_release_manifest

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


def _verify_agent_api_key(settings: Settings, x_agent_api_key: str | None) -> None:
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


@router.post("/checkin", response_model=AgentCheckinResponse)
def checkin(
    payload: AgentCheckinRequest,
    x_agent_api_key: Annotated[str | None, Header(alias="X-Agent-Api-Key")] = None,
) -> AgentCheckinResponse:
    _verify_agent_api_key(get_settings(), x_agent_api_key)

    return process_agent_checkin(payload)


@router.get("/manifest", response_model=AgentManifestResponse)
def manifest(
    hostname: Annotated[str | None, Query()] = None,
    x_agent_api_key: Annotated[str | None, Header(alias="X-Agent-Api-Key")] = None,
) -> AgentManifestResponse:
    settings = get_settings()
    _verify_agent_api_key(settings, x_agent_api_key)

    try:
        version, sha256 = get_agent_release_manifest(settings.agent_release_path)
    except AgentReleaseNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    target_agent_version = get_machine_target_agent_version_by_hostname(hostname) if hostname else None

    return AgentManifestResponse(version=version, sha256=sha256, target_agent_version=target_agent_version)


@router.get("/download")
def download(
    x_agent_api_key: Annotated[str | None, Header(alias="X-Agent-Api-Key")] = None,
) -> Response:
    settings = get_settings()
    _verify_agent_api_key(settings, x_agent_api_key)

    try:
        release_bytes = get_agent_release_bytes(settings.agent_release_path)
    except AgentReleaseNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return Response(content=release_bytes, media_type="application/octet-stream")
