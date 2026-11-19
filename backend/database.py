"""
CyberRakshak AI — MySQL Database Helper
"""
import mysql.connector
from mysql.connector import pooling
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.config import Config

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="cyberrakshak_pool",
            pool_size=5,
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset="utf8mb4",
            autocommit=False,
        )
    return _pool


def get_connection():
    return get_pool().get_connection()


def execute_query(query, params=None, fetch=False, many=False):
    """
    Execute a parameterised SQL query.
    Returns rows when fetch=True, else returns lastrowid.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if many:
            cursor.executemany(query, params or [])
        else:
            cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_db():
    """Create database tables from schema.sql."""
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "database", "schema.sql"
    )
    if not os.path.exists(schema_path):
        return False

    # Connect WITHOUT specifying a database to allow CREATE DATABASE
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    cursor = conn.cursor()
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        # Split on semicolons and execute non-empty statements
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[DB] init_db error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def test_connection():
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False
