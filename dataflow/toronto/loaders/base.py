"""Base loader utilities for database operations."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from dataflow.toronto.models import get_session_factory

T = TypeVar("T")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup.

    Yields:
        SQLAlchemy session that auto-commits on success, rollbacks on error.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def bulk_insert(session: Session, objects: list[T]) -> int:
    """Bulk insert objects into the database.

    Args:
        session: Active SQLAlchemy session.
        objects: List of ORM model instances to insert.

    Returns:
        Number of objects inserted.
    """
    session.add_all(objects)
    session.flush()
    return len(objects)


def upsert_by_key(
    session: Session,
    model_class: Any,
    objects: list[T],
    key_columns: list[str],
) -> tuple[int, int]:
    """Upsert objects based on unique key columns.

    Args:
        session: Active SQLAlchemy session.
        model_class: The ORM model class.
        objects: List of ORM model instances to upsert.
        key_columns: Column names that form the unique key.

    Returns:
        Tuple of (inserted_count, updated_count).
    """
    inserted = 0
    updated = 0

    for obj in objects:
        # Build filter for existing record
        filters = {col: getattr(obj, col) for col in key_columns}
        existing = session.query(model_class).filter_by(**filters).first()

        if existing:
            # Update existing record
            for column in model_class.__table__.columns:
                if column.name not in key_columns and column.name != "id":
                    setattr(existing, column.name, getattr(obj, column.name))
            updated += 1
        else:
            # Insert new record
            session.add(obj)
            inserted += 1

    session.flush()
    return inserted, updated
