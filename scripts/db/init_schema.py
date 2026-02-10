#!/usr/bin/env python3
"""Initialize database schema.

Usage:
    python scripts/db/init_schema.py

This script creates all SQLAlchemy tables in the database.
Run this after docker-compose up to initialize the schema.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from portfolio_app.toronto.models import create_tables, get_engine  # noqa: E402
from portfolio_app.toronto.models.dimensions import RAW_TORONTO_SCHEMA  # noqa: E402


def main() -> int:
    """Initialize the database schema."""
    print("Initializing database schema...")

    try:
        engine = get_engine()

        # Test connection
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("Database connection successful")

        # Create domain-specific schemas
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {RAW_TORONTO_SCHEMA}"))
            conn.commit()
        print(f"Created schema: {RAW_TORONTO_SCHEMA}")

        # Create all tables
        create_tables()
        print("Schema created successfully")

        # List created tables by schema
        from sqlalchemy import inspect

        inspector = inspect(engine)

        # Public schema tables
        public_tables = inspector.get_table_names(schema="public")
        if public_tables:
            print(f"Public schema tables: {', '.join(public_tables)}")

        # raw_toronto schema tables
        toronto_tables = inspector.get_table_names(schema=RAW_TORONTO_SCHEMA)
        if toronto_tables:
            print(f"{RAW_TORONTO_SCHEMA} schema tables: {', '.join(toronto_tables)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
