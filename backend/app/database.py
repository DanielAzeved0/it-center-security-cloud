import os
import threading
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DEFAULT_DATABASE_URL = "postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud"

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("DATABASE_URL must be configured in production")

    return DEFAULT_DATABASE_URL


def get_connection_pool() -> ConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        with _pool_lock:
            if _pool is None or _pool.closed:
                _pool = ConnectionPool(
                    conninfo=get_database_url(),
                    min_size=1,
                    max_size=5,
                    timeout=10.0,
                    max_idle=300.0,
                    kwargs={"row_factory": dict_row},
                    open=True,
                )
    return _pool


def close_connection_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None and not _pool.closed:
            _pool.close()
            _pool = None


@contextmanager
def get_connection():
    pool = get_connection_pool()
    with pool.connection() as connection:
        yield connection
