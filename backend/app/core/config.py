import os


class Settings:
    agent_api_key: str | None

    def __init__(self) -> None:
        self.agent_api_key = os.getenv("AGENT_API_KEY")


def get_settings() -> Settings:
    return Settings()
