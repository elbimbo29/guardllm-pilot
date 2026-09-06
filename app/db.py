import os
from psycopg2.pool import SimpleConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/guardllm")

pool = None

def get_pool():
    global pool
    if pool is None:
        pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
    return pool

def get_db_connection():
    return get_pool().getconn()

def release_db_connection(conn):
    if pool:
        pool.putconn(conn)
