from app.database import close_connection_pool, get_connection, get_connection_pool


def test_connection_pool_reuses_connections():
    close_connection_pool()
    pool = get_connection_pool()
    assert pool.min_size == 1
    assert pool.max_size == 5

    with get_connection() as conn1:
        row1 = conn1.execute("SELECT 1 AS alive").fetchone()
        assert row1["alive"] == 1

    with get_connection() as conn2:
        row2 = conn2.execute("SELECT 2 AS alive").fetchone()
        assert row2["alive"] == 2

    # Verifica que o pool continua ativo e funcional
    assert pool.get_stats()["pool_available"] >= 1
    close_connection_pool()
