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

from dataflow.football.models import Base as FootballBase  # noqa: E402
from dataflow.football.models.dimensions import RAW_FOOTBALL_SCHEMA  # noqa: E402
from dataflow.toronto.models import create_tables as create_toronto_tables  # noqa: E402
from dataflow.toronto.models import get_engine
from dataflow.toronto.models.dimensions import RAW_TORONTO_SCHEMA  # noqa: E402


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

        # Create all schemas upfront — raw schemas for SQLAlchemy tables,
        # dbt schemas as empty shells so grants don't fail before dbt runs
        all_schemas = [
            "shared",
            RAW_TORONTO_SCHEMA, "stg_toronto", "int_toronto", "mart_toronto",
            RAW_FOOTBALL_SCHEMA, "stg_football", "int_football", "mart_football",
        ]
        with engine.connect() as conn:
            for schema in all_schemas:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        print(f"Created schemas: {', '.join(all_schemas)}")

        # Create all Toronto tables
        create_toronto_tables()
        print("Toronto tables created")

        # Create all Football tables
        FootballBase.metadata.create_all(engine)
        print("Football tables created")

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

        # raw_football schema tables
        football_tables = inspector.get_table_names(schema=RAW_FOOTBALL_SCHEMA)
        if football_tables:
            print(f"{RAW_FOOTBALL_SCHEMA} schema tables: {', '.join(football_tables)}")

        # Create portfolio_reader user if not exists (used by pgweb for read-only access)
        with engine.connect() as conn:
            conn.execute(text("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'portfolio_reader') THEN
                        CREATE USER portfolio_reader WITH PASSWORD 'change_me_in_production';
                    END IF;
                END
                $$;
            """))
            conn.commit()
        print("portfolio_reader user ready")

        # Grant portfolio_reader access to all schemas (pgweb read-only user)
        # Covers raw + dbt staging/intermediate/mart layers for all domains
        reader_schemas = [
            "public", "shared",
            RAW_TORONTO_SCHEMA, "stg_toronto", "int_toronto", "mart_toronto",
            RAW_FOOTBALL_SCHEMA, "stg_football", "int_football", "mart_football",
        ]
        with engine.connect() as conn:
            for schema in reader_schemas:
                conn.execute(text(f"GRANT USAGE ON SCHEMA {schema} TO portfolio_reader"))
                conn.execute(text(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO portfolio_reader"))
                conn.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO portfolio_reader"))
            conn.commit()
        print(f"Granted portfolio_reader access to: {', '.join(reader_schemas)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
