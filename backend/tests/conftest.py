import pytest

from app.database import get_connection


@pytest.fixture(autouse=True)
def clean_database():
    with get_connection() as connection:
        with connection.transaction():
            connection.execute(
                """
                TRUNCATE TABLE
                    agent_configs,
                    alerts,
                    security_events,
                    installed_programs,
                    metrics,
                    machines
                RESTART IDENTITY CASCADE
                """
            )

    yield
