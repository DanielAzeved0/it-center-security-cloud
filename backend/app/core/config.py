import os


class Settings:
    agent_api_key: str | None
    app_env: str
    auth_token_secret: str | None
    auth_token_expiration_minutes: int
    agent_release_path: str

    def __init__(self) -> None:
        self.agent_api_key = os.getenv("AGENT_API_KEY")
        self.app_env = os.getenv("APP_ENV", "development").lower()
        self.auth_token_secret = os.getenv("AUTH_TOKEN_SECRET")
        self.auth_token_expiration_minutes = int(os.getenv("AUTH_TOKEN_EXPIRATION_MINUTES", "60"))
        # Populated by `COPY agent-windows/itcenter-agent.ps1` in backend/Dockerfile (EPIC 22).
        self.agent_release_path = os.getenv("AGENT_RELEASE_PATH", "/app/agent-release/itcenter-agent.ps1")

    def validate_runtime_configuration(self) -> None:
        """Fail fast when an unsafe production configuration reaches the API."""
        if self.app_env != "production":
            return

        database_url = os.getenv("DATABASE_URL")
        insecure_values = {None, "", "change-me", "CHANGE_ME", "replace-me"}

        if self.agent_api_key in insecure_values:
            raise RuntimeError("AGENT_API_KEY must be configured with a non-default value in production")

        if self.auth_token_secret in insecure_values:
            raise RuntimeError("AUTH_TOKEN_SECRET must be configured with a non-default value in production")

        if not database_url:
            raise RuntimeError("DATABASE_URL must be configured in production")

        if "change-me" in database_url or "replace-me" in database_url:
            raise RuntimeError("DATABASE_URL must not contain a default password in production")


def get_settings() -> Settings:
    return Settings()
