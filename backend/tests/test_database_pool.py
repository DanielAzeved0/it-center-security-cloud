import pytest
from app.database import close_connection_pool, get_connection, get_connection_pool
import app.database as db_mod
from app.main import app, lifespan


def test_connection_pool_reuses_connections():
    close_connection_pool()
    pool = get_connection_pool()
    assert pool.min_size == 1
    assert pool.max_size == 5

    with get_connection() as conn1:
        row1 = conn1.execute("SELECT 1 AS alive, pg_backend_pid() AS pid").fetchone()
        assert row1["alive"] == 1
        pid1 = row1["pid"]

    with get_connection() as conn2:
        row2 = conn2.execute("SELECT 2 AS alive, pg_backend_pid() AS pid").fetchone()
        assert row2["alive"] == 2
        pid2 = row2["pid"]

    # Verifica que a mesma conexao ativa do PostgreSQL foi reaproveitada pelo pool
    assert pid1 == pid2

    # Verifica que o pool continua ativo e funcional
    assert pool.get_stats()["pool_available"] >= 1
    close_connection_pool()


@pytest.mark.anyio
async def test_lifespan_closes_connection_pool():
    # Initialize pool
    pool = get_connection_pool()
    assert not pool.closed

    async with lifespan(app):
        assert not pool.closed

    assert db_mod._pool is None

