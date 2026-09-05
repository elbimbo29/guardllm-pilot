import os
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:adminpass@localhost:5432/guardllm_db"
)

# Initialize a thread-safe connection pool
pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

@contextmanager
def get_db_connection():
    """Provides a transactional database connection from the pool."""
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)