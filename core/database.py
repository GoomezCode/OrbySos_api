import mysql.connector
from mysql.connector import pooling
from core.config import get_settings

_pool: pooling.MySQLConnectionPool | None = None


def get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = pooling.MySQLConnectionPool(
            pool_name="orbyt_pool",
            pool_size=5,
            pool_reset_session=True,
            host=settings.db_host,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            port=settings.db_port,
            auth_plugin="mysql_native_password",
        )
    return _pool


def get_connection() -> mysql.connector.MySQLConnection:
    return get_pool().get_connection()
