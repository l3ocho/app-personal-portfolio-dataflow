#!/usr/bin/env python3
"""Add indexes on fact_rentals FK columns for optimal join performance.

While FK columns are part of the composite unique index, dedicated single-column
indexes provide optimal performance for FK constraint checks and joins.

Migration: add_fk_indexes
Date: 2026-02-11
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text

from dataflow.toronto.models import get_engine


def main() -> int:
    """Add indexes on fact_rentals FK columns."""
    print("Adding indexes on fact_rentals FK columns...")

    engine = get_engine()

    # Define indexes to add (use CONCURRENTLY to avoid table locks)
    indexes = [
        {
            "name": "ix_fact_rentals_date_key",
            "table": "fact_rentals",
            "column": "date_key",
        },
        {
            "name": "ix_fact_rentals_zone_key",
            "table": "fact_rentals",
            "column": "zone_key",
        },
    ]

    try:
        # Note: CONCURRENTLY requires autocommit mode
        with engine.connect() as conn:
            # Set autocommit for CONCURRENTLY
            conn.execute(text("COMMIT"))

            for idx in indexes:
                # Check if index already exists
                check_sql = text(
                    """
                    SELECT 1 FROM pg_indexes
                    WHERE schemaname = 'raw_toronto'
                    AND tablename = :table
                    AND indexname = :index
                """
                )
                result = conn.execute(
                    check_sql,
                    {"table": idx["table"], "index": idx["name"]},
                )
                exists = result.fetchone() is not None

                if exists:
                    print(
                        f"  ⊘ {idx['name']} already exists on {idx['table']}, skipping"
                    )
                    continue

                # Create index CONCURRENTLY (no table lock)
                create_sql = text(
                    f"""
                    CREATE INDEX CONCURRENTLY {idx['name']}
                    ON raw_toronto.{idx['table']} ({idx['column']})
                """
                )

                conn.execute(create_sql)
                print(
                    f"  ✓ Created index {idx['name']} on {idx['table']}.{idx['column']}"
                )

        # Verify indexes created
        with engine.connect() as conn:
            verify_sql = text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'raw_toronto' AND tablename = 'fact_rentals'
                ORDER BY indexname
            """
            )
            result = conn.execute(verify_sql)
            indexes_list = result.fetchall()

            print(f"\nFinal indexes on raw_toronto.fact_rentals: {len(indexes_list)}")
            for idx in indexes_list:
                print(f"  - {idx[0]}")

        print("\n✓ Migration completed successfully")
        return 0

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
