"""
Database helper utilities.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import Config

_cfg = Config()
engine = create_engine(_cfg.MYSQL_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def execute_query(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return result.fetchall()


def execute_update(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        conn.commit()
        return result.rowcount


def execute_insert(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        conn.commit()
        return result.lastrowid
