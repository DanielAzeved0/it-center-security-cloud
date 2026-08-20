import hashlib

from fastapi.testclient import TestClient

from app.database import get_connection
from app.main import app
from tests.test_agent_checkin import VALID_PAYLOAD

RELEASE_CONTENT = 'param()\n$script:AgentVersion = "1.2.3"\nWrite-Output "hello"\n'


def _write_release_fixture(tmp_path, monkeypatch, content: str = RELEASE_CONTENT):
    release_path = tmp_path / "itcenter-agent.ps1"
    release_path.write_text(content, encoding="utf-8")
    monkeypatch.setenv("AGENT_RELEASE_PATH", str(release_path))
    return release_path


def test_manifest_returns_version_and_sha256(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    release_path = _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/v1/agent/manifest", headers={"X-Agent-Api-Key": "test-key"})

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.2.3"
    assert body["sha256"] == hashlib.sha256(release_path.read_bytes()).hexdigest()
    assert body["target_agent_version"] is None


def test_manifest_rejects_missing_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/v1/agent/manifest")

    assert response.status_code == 401


def test_manifest_rejects_wrong_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/v1/agent/manifest", headers={"X-Agent-Api-Key": "wrong-key"})

    assert response.status_code == 401


def test_manifest_returns_500_when_release_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_RELEASE_PATH", str(tmp_path / "does-not-exist.ps1"))
    client = TestClient(app)

    response = client.get("/api/v1/agent/manifest", headers={"X-Agent-Api-Key": "test-key"})

    assert response.status_code == 500


def test_manifest_returns_target_agent_version_for_known_hostname(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    checkin_response = client.post(
        "/api/v1/agent/checkin",
        json=VALID_PAYLOAD,
        headers={"X-Agent-Api-Key": "test-key"},
    )
    machine_id = checkin_response.json()["machine_id"]

    with get_connection() as connection:
        connection.execute(
            "UPDATE machines SET target_agent_version = %s WHERE id = %s",
            ("1.0.0", machine_id),
        )

    response = client.get(
        "/api/v1/agent/manifest",
        params={"hostname": VALID_PAYLOAD["hostname"]},
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json()["target_agent_version"] == "1.0.0"


def test_manifest_returns_null_target_version_for_unknown_hostname(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/api/v1/agent/manifest",
        params={"hostname": "PC-NAO-CADASTRADO"},
        headers={"X-Agent-Api-Key": "test-key"},
    )

    assert response.status_code == 200
    assert response.json()["target_agent_version"] is None


def test_download_returns_bytes_matching_manifest_sha256(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    manifest_response = client.get("/api/v1/agent/manifest", headers={"X-Agent-Api-Key": "test-key"})
    download_response = client.get("/api/v1/agent/download", headers={"X-Agent-Api-Key": "test-key"})

    assert download_response.status_code == 200
    assert hashlib.sha256(download_response.content).hexdigest() == manifest_response.json()["sha256"]


def test_download_rejects_missing_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    _write_release_fixture(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/v1/agent/download")

    assert response.status_code == 401
