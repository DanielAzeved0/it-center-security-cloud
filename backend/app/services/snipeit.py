"""Integracao com o Snipe-IT (EPIC 19, ADR-028).

O Snipe-IT e a fonte oficial de ITAM (patrimonio, garantia, licencas,
historico de movimentacao). O IT Center armazena apenas
`machines.snipeit_asset_id` como referencia e sincroniza automaticamente
maquinas novas detectadas pelo agente. Falha de comunicacao com o Snipe-IT
nao deve bloquear o check-in do agente: qualquer erro e apenas logado.
"""

import logging

import httpx

from app.core.config import get_settings
from app.repositories.machines import update_machine_snipeit_asset_id

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 10.0


def is_snipeit_configured() -> bool:
    settings = get_settings()
    return bool(settings.snipeit_base_url and settings.snipeit_api_token)


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.snipeit_api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _api_base_url() -> str:
    settings = get_settings()
    base_url = (settings.snipeit_base_url or "").rstrip("/")
    return f"{base_url}/api/v1"


def find_asset_by_hostname(client: httpx.Client, hostname: str) -> int | None:
    response = client.get(
        f"{_api_base_url()}/hardware",
        headers=_auth_headers(),
        params={"search": hostname},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    payload = response.json()
    rows = payload.get("rows") or []

    for row in rows:
        name = row.get("name")
        asset_id = row.get("id")
        if isinstance(name, str) and name.strip().lower() == hostname.strip().lower() and isinstance(asset_id, int):
            return asset_id

    return None


def create_asset(client: httpx.Client, hostname: str) -> int | None:
    settings = get_settings()

    if not settings.snipeit_default_model_id or not settings.snipeit_default_status_id:
        logger.info(
            "Snipe-IT: criacao de ativo pulada para %s por falta de "
            "SNIPEIT_DEFAULT_MODEL_ID/SNIPEIT_DEFAULT_STATUS_ID configurados.",
            hostname,
        )
        return None

    response = client.post(
        f"{_api_base_url()}/hardware",
        headers=_auth_headers(),
        json={
            "name": hostname,
            "model_id": settings.snipeit_default_model_id,
            "status_id": settings.snipeit_default_status_id,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    payload = response.json()
    asset_id = payload.get("payload", {}).get("id")
    return asset_id if isinstance(asset_id, int) else None


def update_asset(client: httpx.Client, asset_id: int, hostname: str) -> None:
    response = client.patch(
        f"{_api_base_url()}/hardware/{asset_id}",
        headers=_auth_headers(),
        json={"name": hostname},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def sync_machine_asset(machine_id: int, hostname: str) -> None:
    if not is_snipeit_configured():
        return

    try:
        with httpx.Client() as client:
            asset_id = find_asset_by_hostname(client, hostname)

            if asset_id is not None:
                update_asset(client, asset_id, hostname)
                update_machine_snipeit_asset_id(machine_id, asset_id)
                return

            created_asset_id = create_asset(client, hostname)

            if created_asset_id is not None:
                update_machine_snipeit_asset_id(machine_id, created_asset_id)
    except Exception as exc:  # noqa: BLE001 - integracao nao pode derrubar o check-in do agente
        logger.warning(
            "Snipe-IT: falha ao sincronizar ativo para a maquina %s (id=%s): %s",
            hostname,
            machine_id,
            exc,
        )
