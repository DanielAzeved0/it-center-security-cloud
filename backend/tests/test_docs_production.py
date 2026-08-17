"""EPIC 28: docs_url/redoc_url/openapi_url devem ser desativados quando
APP_ENV=production, como segunda camada de defesa contra qualquer bypass de
path traversal no proxy que consiga alcancar esses caminhos diretamente.

app.main.app e construido em tempo de import, entao o unico jeito de testar
os dois cenarios (dev/producao) e recarregar o modulo com APP_ENV alterado.
"""

import importlib

from fastapi.testclient import TestClient


def _reload_main():
    import app.main as main_module

    return importlib.reload(main_module)


def test_docs_enabled_outside_production(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    main_module = _reload_main()
    client = TestClient(main_module.app)

    try:
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200
        assert client.get("/openapi.json").status_code == 200
    finally:
        _reload_main()


def test_docs_disabled_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    main_module = _reload_main()
    client = TestClient(main_module.app)

    try:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/api/v1/health").status_code == 200
    finally:
        monkeypatch.delenv("APP_ENV", raising=False)
        _reload_main()
