#!/usr/bin/env python3
"""Idempotent schema migrations run on every deployment.

Handles:
- Dropping mart tables renamed in dbt (dbt does not auto-drop on rename)
- Adding columns added to existing raw tables (SQLAlchemy create_all skips existing tables)

All operations are idempotent — safe to run multiple times.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text

from dataflow.toronto.models import get_engine

RENAMED_TABLES = [
    # (schema, old_name)
    ("mart_toronto", "mart_toronto__neighbourhood_profile"),
]

# Columns added to existing tables after initial schema creation.
# Format: (schema, table, column, column_definition)
MISSING_COLUMNS = [
    # Sprint 12: added hierarchy columns to fact_neighbourhood_profile
    ("raw_toronto", "fact_neighbourhood_profile", "category_total", "INTEGER NULL"),
    ("raw_toronto", "fact_neighbourhood_profile", "indent_level", "SMALLINT NOT NULL DEFAULT 0"),
]


def main() -> int:
    engine = get_engine()
    with engine.begin() as conn:
        for schema, table in RENAMED_TABLES:
            conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table}"'))
            print(f"Dropped {schema}.{table} (if existed)")

        for schema, table, column, definition in MISSING_COLUMNS:
            conn.execute(text(
                f"ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS {column} {definition}"
            ))
            print(f"Ensured column {schema}.{table}.{column}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
