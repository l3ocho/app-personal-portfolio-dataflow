#!/usr/bin/env python3
"""Add composite unique constraints on natural keys.

All natural key combinations verified to be unique before applying.

Migration: add_unique_constraints
Date: 2026-02-11
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text

from dataflow.toronto.models import get_engine


def main() -> int:
    """Add composite unique constraints on natural keys."""
    print("Adding composite unique constraints to raw_toronto schema...")

    engine = get_engine()

    # Define unique constraints to add
    constraints = [
        {
            "table": "fact_census",
            "constraint": "uq_fact_census_natural_key",
            "columns": ["neighbourhood_id", "census_year"],
        },
        {
            "table": "fact_crime",
            "constraint": "uq_fact_crime_natural_key",
            "columns": ["neighbourhood_id", "year", "crime_type"],
        },
        {
            "table": "fact_amenities",
            "constraint": "uq_fact_amenities_natural_key",
            "columns": ["neighbourhood_id", "amenity_type", "year"],
        },
        {
            "table": "fact_rentals",
            "constraint": "uq_fact_rentals_natural_key",
            "columns": ["zone_key", "bedroom_type", "date_key"],
        },
        {
            "table": "bridge_cmhc_neighbourhood",
            "constraint": "uq_bridge_cmhc_neighbourhood_natural_key",
            "columns": ["cmhc_zone_code", "neighbourhood_id"],
        },
    ]

    try:
        with engine.connect() as conn:
            for uq in constraints:
                # Check if constraint already exists
                check_sql = text(
                    """
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_schema = 'raw_toronto'
                    AND table_name = :table
                    AND constraint_name = :constraint
                    AND constraint_type = 'UNIQUE'
                """
                )
                result = conn.execute(
                    check_sql,
                    {"table": uq["table"], "constraint": uq["constraint"]},
                )
                exists = result.fetchone() is not None

                if exists:
                    print(
                        f"  ⊘ {uq['constraint']} already exists on {uq['table']}, skipping"
                    )
                    continue

                # Add unique constraint
                columns_list = ", ".join(uq["columns"])
                alter_sql = text(
                    f"""
                    ALTER TABLE raw_toronto.{uq['table']}
                    ADD CONSTRAINT {uq['constraint']}
                    UNIQUE ({columns_list})
                """
                )

                conn.execute(alter_sql)
                conn.commit()
                print(
                    f"  ✓ Added {uq['constraint']} on {uq['table']}({columns_list})"
                )

        # Verify final unique constraint count
        with engine.connect() as conn:
            count_sql = text(
                """
                SELECT COUNT(*) AS uq_count
                FROM information_schema.table_constraints
                WHERE constraint_type = 'UNIQUE'
                AND table_schema = 'raw_toronto'
            """
            )
            result = conn.execute(count_sql)
            uq_count = result.fetchone()[0]
            print(f"\nFinal UNIQUE constraint count in raw_toronto: {uq_count}")

        print("\n✓ Migration completed successfully")
        return 0

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
