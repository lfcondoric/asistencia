import logging
from contextlib import contextmanager
from typing import Generator
import pymysql
from pymysql.cursors import DictCursor
from app.config import settings

logger = logging.getLogger(__name__)


def get_db_connection() -> pymysql.Connection:
    """Crea y retorna una conexión directa a MySQL usando PyMySQL."""
    try:
        connect_kwargs = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_NAME,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": True,
            "connect_timeout": 5,
        }
        if settings.DB_SSL:
            connect_kwargs["ssl"] = {"ssl_mode": "REQUIRED"}

        connection = pymysql.connect(**connect_kwargs)
        return connection
    except pymysql.MySQLError as e:
        logger.error(f"Error de conexión a la base de datos MySQL: {e}")
        raise e


@contextmanager
def get_db_cursor() -> Generator[DictCursor, None, None]:
    """Context manager para obtener un cursor con liberación automática de recursos."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
    finally:
        conn.close()
