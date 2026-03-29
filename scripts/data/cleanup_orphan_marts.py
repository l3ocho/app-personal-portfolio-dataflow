#!/usr/bin/env python3
"""Detect and drop orphaned mart tables.

An orphaned mart table is a table that exists in a mart schema in the database
but has no corresponding .sql model file under dbt/models/marts/.

This replaces the need for manually curated deprecated-table lists. After any
dbt model removal, run this script (or let make dbt-run call it) to drop
the leftover table automatically.

Usage:
    python scripts/data/cleanup_orphan_marts.py           # dry run
    python scripts/data/cleanup_orphan_marts.py --execute # actually drop orphans
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from dataflow.toronto.loaders import get_session  # noqa: E402

DBT_MARTS_DIR = PROJECT_ROOT / "dbt" / "models" / "marts"
MART_SCHEMAS = ["mart_toronto", "mart_football"]


def get_expected_tables() -> set[str]:
    """Return model names from .sql files under dbt/models/marts/."""
    return {f.stem for f in DBT_MARTS_DIR.rglob("*.sql")}


def get_actual_tables(schema: str) -> list[str]:
    """Return table names that exist in the given PostgreSQL schema."""
    with get_session() as session:
        result = session.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = :schema ORDER BY tablename"
            ),
            {"schema": schema},
        )
        return [row[0] for row in result]


def find_orphans() -> dict[str, list[str]]:
    """Compare DB tables against dbt model files; return orphans by schema."""
    expected = get_expected_tables()
    orphans: dict[str, list[str]] = {}

    for schema in MART_SCHEMAS:
        try:
            actual = get_actual_tables(schema)
        except Exception as exc:
            print(f"⚠️  Could not query schema {schema}: {exc}")
            continue
        schema_orphans = [t for t in actual if t not in expected]
        if schema_orphans:
            orphans[schema] = schema_orphans

    return orphans


def drop_orphans(orphans: dict[str, list[str]]) -> None:
    """Drop all orphaned tables with CASCADE."""
    with get_session() as session:
        for schema, tables in orphans.items():
            for table in tables:
                try:
                    session.execute(
                        text(f"DROP TABLE IF EXISTS {schema}.{table} CASCADE")
                    )
                    session.commit()
                    print(f"✅ Dropped orphan: {schema}.{table}")
                except Exception as exc:
                    print(f"⚠️  Could not drop {schema}.{table}: {exc}")
                    session.rollback()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually drop orphaned tables (default: dry run only)",
    )
    args = parser.parse_args()

    print("🔍 Scanning for orphaned mart tables...")
    orphans = find_orphans()

    if not any(orphans.values()):
        print("✅ No orphaned mart tables found.")
        return

    print("\nOrphaned tables detected:")
    for schema, tables in orphans.items():
        for table in tables:
            print(f"  ⚠️  {schema}.{table}")

    if args.execute:
        print("\nDropping orphaned tables...")
        drop_orphans(orphans)
        print("\n✅ Orphan cleanup complete.")
    else:
        print(
            "\n(Dry run — run with --execute to drop these tables, "
            "or: make cleanup-orphan-marts ARGS=--execute)"
        )


if __name__ == "__main__":
    main()
