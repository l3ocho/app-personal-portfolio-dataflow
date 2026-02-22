"""SQLAlchemy base configuration for football models."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from dataflow.config import get_settings


class Base(DeclarativeBase):  # type: ignore[misc]
    """Base class for all football SQLAlchemy models."""

    pass


def get_engine() -> Engine:
    """Create database engine from settings."""
    settings = get_settings()
    return create_engine(settings.database_url, echo=False)


def get_session_factory() -> sessionmaker[Session]:
    """Create session factory for football models."""
    engine = get_engine()
    return sessionmaker(bind=engine)
