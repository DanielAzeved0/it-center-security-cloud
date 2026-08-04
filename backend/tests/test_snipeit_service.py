import httpx

from app.database import get_connection
from app.services import snipeit as snipeit_service


class FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://snipeit.example.com")
            raise httpx.HTTPStatusError(
                "error",
                request=request,
                response=httpx.Response(self.status_code, request=request),
            )

    def json(self) -> dict:
        return self._json_data


class FakeClient:
    def __init__(self, *, get_response=None, post_response=None, patch_response=None, raise_exc=None):
        self.get_response = get_response
        self.post_response = post_response
        self.patch_response = patch_response
        self.raise_exc = raise_exc
        self.calls: list[tuple[str, str, dict]] = []

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args) -> bool:
        return False

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if self.raise_exc:
            raise self.raise_exc
        return self.get_response

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if self.raise_exc:
            raise self.raise_exc
        return self.post_response

    def patch(self, url, **kwargs):
        self.calls.append(("PATCH", url, kwargs))
        if self.raise_exc:
            raise self.raise_exc
        return self.patch_response


def _configure_snipeit(monkeypatch, *, model_id: int | None = None, status_id: int | None = None) -> None:
    monkeypatch.setenv("SNIPEIT_BASE_URL", "https://snipeit.example.com")
    monkeypatch.setenv("SNIPEIT_API_TOKEN", "test-token")

    if model_id is not None:
        monkeypatch.setenv("SNIPEIT_DEFAULT_MODEL_ID", str(model_id))
    else:
        monkeypatch.delenv("SNIPEIT_DEFAULT_MODEL_ID", raising=False)

    if status_id is not None:
        monkeypatch.setenv("SNIPEIT_DEFAULT_STATUS_ID", str(status_id))
    else:
        monkeypatch.delenv("SNIPEIT_DEFAULT_STATUS_ID", raising=False)


def _insert_machine(hostname: str) -> int:
    with get_connection() as connection:
        return connection.execute(
            """
            INSERT INTO machines (hostname, status)
            VALUES (%s, 'online')
            RETURNING id
            """,
            (hostname,),
        ).fetchone()["id"]


def _get_snipeit_asset_id(machine_id: int) -> int | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT snipeit_asset_id FROM machines WHERE id = %s",
            (machine_id,),
        ).fetchone()

    return row["snipeit_asset_id"]


def test_is_snipeit_configured_false_when_missing_settings(monkeypatch):
    monkeypatch.delenv("SNIPEIT_BASE_URL", raising=False)
    monkeypatch.delenv("SNIPEIT_API_TOKEN", raising=False)

    assert snipeit_service.is_snipeit_configured() is False


def test_is_snipeit_configured_true_when_base_url_and_token_set(monkeypatch):
    _configure_snipeit(monkeypatch)

    assert snipeit_service.is_snipeit_configured() is True


def test_sync_disabled_integration_makes_no_http_calls(monkeypatch):
    monkeypatch.delenv("SNIPEIT_BASE_URL", raising=False)
    monkeypatch.delenv("SNIPEIT_API_TOKEN", raising=False)

    def fail_if_instantiated(*args, **kwargs):
        raise AssertionError("httpx.Client nao deveria ser instanciado com a integracao desativada")

    monkeypatch.setattr(snipeit_service.httpx, "Client", fail_if_instantiated)

    machine_id = _insert_machine("PC-TESTE-DISABLED")

    snipeit_service.sync_machine_asset(machine_id, "PC-TESTE-DISABLED")

    assert _get_snipeit_asset_id(machine_id) is None


def test_sync_updates_asset_found_by_hostname_search(monkeypatch):
    _configure_snipeit(monkeypatch)
    machine_id = _insert_machine("PC-TESTE-FOUND")

    fake_client = FakeClient(
        get_response=FakeResponse({"rows": [{"id": 42, "name": "PC-TESTE-FOUND"}]}),
        patch_response=FakeResponse({"status": "success"}),
    )
    monkeypatch.setattr(snipeit_service.httpx, "Client", lambda *a, **kw: fake_client)

    snipeit_service.sync_machine_asset(machine_id, "PC-TESTE-FOUND")

    assert [call[0] for call in fake_client.calls] == ["GET", "PATCH"]
    assert _get_snipeit_asset_id(machine_id) == 42


def test_sync_creates_asset_when_not_found_and_defaults_configured(monkeypatch):
    _configure_snipeit(monkeypatch, model_id=10, status_id=20)
    machine_id = _insert_machine("PC-TESTE-CREATE")

    fake_client = FakeClient(
        get_response=FakeResponse({"rows": []}),
        post_response=FakeResponse({"payload": {"id": 99}}),
    )
    monkeypatch.setattr(snipeit_service.httpx, "Client", lambda *a, **kw: fake_client)

    snipeit_service.sync_machine_asset(machine_id, "PC-TESTE-CREATE")

    assert [call[0] for call in fake_client.calls] == ["GET", "POST"]
    create_call = fake_client.calls[1]
    assert create_call[2]["json"] == {
        "name": "PC-TESTE-CREATE",
        "model_id": 10,
        "status_id": 20,
    }
    assert _get_snipeit_asset_id(machine_id) == 99


def test_sync_skips_creation_when_defaults_not_configured(monkeypatch):
    _configure_snipeit(monkeypatch)
    machine_id = _insert_machine("PC-TESTE-NODEFAULTS")

    fake_client = FakeClient(get_response=FakeResponse({"rows": []}))
    monkeypatch.setattr(snipeit_service.httpx, "Client", lambda *a, **kw: fake_client)

    snipeit_service.sync_machine_asset(machine_id, "PC-TESTE-NODEFAULTS")

    assert [call[0] for call in fake_client.calls] == ["GET"]
    assert _get_snipeit_asset_id(machine_id) is None


def test_sync_swallows_connection_error_without_propagating(monkeypatch):
    _configure_snipeit(monkeypatch)
    machine_id = _insert_machine("PC-TESTE-ERROR")

    fake_client = FakeClient(raise_exc=httpx.ConnectError("connection refused"))
    monkeypatch.setattr(snipeit_service.httpx, "Client", lambda *a, **kw: fake_client)

    # Nao deve levantar excecao para fora de sync_machine_asset.
    snipeit_service.sync_machine_asset(machine_id, "PC-TESTE-ERROR")

    assert _get_snipeit_asset_id(machine_id) is None
