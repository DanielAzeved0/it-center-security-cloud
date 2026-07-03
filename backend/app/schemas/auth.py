from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    id: int
    email: str
    name: str
    role: str


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: AuthUser


class CurrentUserResponse(BaseModel):
    user: AuthUser


class LogoutResponse(BaseModel):
    status: str
    message: str
