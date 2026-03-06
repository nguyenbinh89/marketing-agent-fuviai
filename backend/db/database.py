"""
FuviAI Marketing Agent — Database Setup
SQLAlchemy async engine + session factory
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from loguru import logger


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        from backend.config.settings import get_settings
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=settings.app_env == "development",
        )
        logger.info("Database engine created")
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager cho DB session — auto commit/rollback/close."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Tạo tất cả bảng nếu chưa tồn tại (dùng trong dev/test)."""
    from backend.db import models  # noqa: F401 — ensure models registered
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database tables created")
