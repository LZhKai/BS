"""
数据库工具类
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import Config

# 创建数据库引擎
engine = create_engine(Config.MYSQL_URL, pool_pre_ping=True)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_query(sql, params=None):
    """执行查询"""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return result.fetchall()

def execute_update(sql, params=None):
    """执行更新"""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        conn.commit()
        return result.rowcount

