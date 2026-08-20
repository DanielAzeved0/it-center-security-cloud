import hashlib
import re
from pathlib import Path

_VERSION_PATTERN = re.compile(r'^\s*\$script:AgentVersion\s*=\s*"([^"]+)"', re.MULTILINE)


class AgentReleaseNotConfigured(Exception):
    pass


def _read_release_bytes(release_path: str) -> bytes:
    path = Path(release_path)
    if not path.is_file():
        raise AgentReleaseNotConfigured(f"Agent release file not found: {release_path}")

    return path.read_bytes()


def _extract_version(release_bytes: bytes) -> str:
    match = _VERSION_PATTERN.search(release_bytes.decode("utf-8"))
    if not match:
        raise AgentReleaseNotConfigured("$script:AgentVersion not found in agent release file")

    return match.group(1)


def get_agent_release_manifest(release_path: str) -> tuple[str, str]:
    """Returns (version, sha256) for the agent script currently published by this backend."""
    release_bytes = _read_release_bytes(release_path)
    version = _extract_version(release_bytes)
    sha256 = hashlib.sha256(release_bytes).hexdigest()
    return version, sha256


def get_agent_release_bytes(release_path: str) -> bytes:
    return _read_release_bytes(release_path)
