from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import HTTPException

from app.repositories.audit_logs import create_audit_log
from app.repositories.users import get_user_by_email, mark_user_login
from app.schemas.auth import AuthUser, CurrentUserResponse, LoginRequest, LoginResponse, LogoutResponse
from app.services.auth import CurrentUser, create_access_token, get_current_user, hash_password, request_ip, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Hash dummy pre-computado uma unica vez na importacao do modulo (nao a cada
# request) para que o login sempre rode o PBKDF2 (210.000 iteracoes), mesmo
# quando o usuario nao existe. Sem isso, o curto-circuito do "or" abaixo
# pulava verify_password para e-mails nao cadastrados, criando uma diferenca
# de tempo de resposta que permitia enumerar e-mails validos (EPIC 28).
_DUMMY_PASSWORD_HASH = hash_password("itcenter-dummy-password-for-timing-equalization")


def _auth_user_from_current_user(user: CurrentUser) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    user = get_user_by_email(payload.email.strip())
    user_agent = request.headers.get("User-Agent")
    ip_address = request_ip(request)

    # verify_password roda sempre, mesmo quando o usuario nao existe (contra
    # o hash dummy), para que o tempo de resposta nao revele se o e-mail
    # esta cadastrado. O resultado funcional nao muda: so autentica usuario
    # ativo com senha correta.
    password_hash = user["password_hash"] if user is not None else _DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(payload.password, password_hash)

    if user is None or user["status"] != "active" or not password_is_valid:
        create_audit_log(
            actor_user_id=None,
            action="auth.login_failed",
            entity_type="auth",
            entity_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": payload.email.strip().lower()},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token, expires_in = create_access_token(user_id=user["id"])
    mark_user_login(user["id"])
    create_audit_log(
        actor_user_id=user["id"],
        action="auth.login",
        entity_type="user",
        entity_id=str(user["id"]),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={},
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=AuthUser(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
        ),
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(user=_auth_user_from_current_user(current_user))


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, current_user: CurrentUser = Depends(get_current_user)) -> LogoutResponse:
    create_audit_log(
        actor_user_id=current_user.id,
        action="auth.logout",
        entity_type="user",
        entity_id=str(current_user.id),
        ip_address=request_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={},
    )

    return LogoutResponse(status="success", message="Logged out")
