import os

import psycopg
from psycopg.rows import dict_row

DEFAULT_DATABASE_URL = "postgresql://itcenter:change-me@127.0.0.1:5432/it_center_security_cloud"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_connection():
    return psycopg.connect(get_database_url(), row_factory=dict_row)
