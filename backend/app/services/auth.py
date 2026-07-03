import base64
import hashlib
import hmac
import ipaddress
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.repositories.users import get_user_by_id

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 210_000
TOKEN_ALGORITHM = "HS256"
DEFAULT_DEVELOPMENT_SECRET = "development-auth-secret-change-in-production"

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: int
    email: str
    name: str
    role: str


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _auth_secret() -> str:
    return get_settings().auth_token_secret or DEFAULT_DEVELOPMENT_SECRET


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)

    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(PASSWORD_ITERATIONS),
            _base64url_encode(salt),
            _base64url_encode(digest),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_value, salt_value, digest_value = password_hash.split("$", 3)
        iterations = int(iterations_value)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    salt = _base64url_decode(salt_value)
    expected_digest = _base64url_decode(digest_value)
    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(*, user_id: int, expires_in_seconds: int | None = None) -> tuple[str, int]:
    expires_in = expires_in_seconds or get_settings().auth_token_expiration_minutes * 60
    issued_at = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": issued_at + expires_in,
    }
    header = {"alg": TOKEN_ALGORITHM, "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(_auth_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()

    return f"{signing_input}.{_base64url_encode(signature)}", expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_value, payload_value, signature_value = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Malformed token") from exc

    signing_input = f"{header_value}.{payload_value}"
    expected_signature = hmac.new(
        _auth_secret().encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(expected_signature, _base64url_decode(signature_value)):
        raise ValueError("Invalid token signature")

    payload = json.loads(_base64url_decode(payload_value))

    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("Token expired")

    return payload


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise authentication_error()

    user = get_user_by_id(user_id)

    if user is None or user["status"] != "active":
        raise authentication_error()

    return CurrentUser(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
    )


def require_roles(*roles: str):
    allowed_roles = set(roles)

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def request_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        candidate = forwarded_for.split(",", 1)[0].strip()
    else:
        candidate = request.client.host if request.client else None

    if not candidate:
        return None

    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None

    return candidate
