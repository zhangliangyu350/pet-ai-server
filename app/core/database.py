from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str = None):
    """根据显式参数或配置的数据库地址创建 SQLAlchemy 引擎。"""
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True, future=True)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """提供请求级数据库会话，并在使用后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
