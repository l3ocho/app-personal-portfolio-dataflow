#!/usr/bin/env python3
"""Add missing foreign key constraints to raw_toronto tables.

This migration adds FK constraints for referential integrity enforcement.
All relationships verified to have 0 orphaned records before applying.

Migration: add_foreign_keys
Date: 2026-02-11
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import text

from dataflow.toronto.models import get_engine


def main() -> int:
    """Add missing foreign key constraints."""
    print("Adding foreign key constraints to raw_toronto schema...")

    engine = get_engine()

    # Define FK constraints to add
    constraints = [
        {
            "table": "fact_census",
            "constraint": "fk_fact_census_neighbourhood",
            "column": "neighbourhood_id",
            "ref_table": "dim_neighbourhood",
            "ref_column": "neighbourhood_id",
        },
        {
            "table": "fact_crime",
            "constraint": "fk_fact_crime_neighbourhood",
            "column": "neighbourhood_id",
            "ref_table": "dim_neighbourhood",
            "ref_column": "neighbourhood_id",
        },
        {
            "table": "fact_amenities",
            "constraint": "fk_fact_amenities_neighbourhood",
            "column": "neighbourhood_id",
            "ref_table": "dim_neighbourhood",
            "ref_column": "neighbourhood_id",
        },
        {
            "table": "bridge_cmhc_neighbourhood",
            "constraint": "fk_bridge_cmhc_neighbourhood_neighbourhood",
            "column": "neighbourhood_id",
            "ref_table": "dim_neighbourhood",
            "ref_column": "neighbourhood_id",
        },
        {
            "table": "bridge_cmhc_neighbourhood",
            "constraint": "fk_bridge_cmhc_neighbourhood_cmhc_zone",
            "column": "cmhc_zone_code",
            "ref_table": "dim_cmhc_zone",
            "ref_column": "zone_code",
        },
    ]

    try:
        with engine.connect() as conn:
            for fk in constraints:
                # Check if constraint already exists
                check_sql = text(
                    """
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_schema = 'raw_toronto'
                    AND table_name = :table
                    AND constraint_name = :constraint
                    AND constraint_type = 'FOREIGN KEY'
                """
                )
                result = conn.execute(
                    check_sql,
                    {"table": fk["table"], "constraint": fk["constraint"]},
                )
                exists = result.fetchone() is not None

                if exists:
                    print(
                        f"  ⊘ {fk['constraint']} already exists on {fk['table']}, skipping"
                    )
                    continue

                # Add FK constraint
                alter_sql = text(
                    f"""
                    ALTER TABLE raw_toronto.{fk["table"]}
                    ADD CONSTRAINT {fk["constraint"]}
                    FOREIGN KEY ({fk["column"]})
                    REFERENCES raw_toronto.{fk["ref_table"]}({fk["ref_column"]})
                """
                )

                conn.execute(alter_sql)
                conn.commit()
                print(
                    f"  ✓ Added {fk['constraint']} on {fk['table']}.{fk['column']} → {fk['ref_table']}.{fk['ref_column']}"
                )

        # Verify final FK count
        with engine.connect() as conn:
            count_sql = text(
                """
                SELECT COUNT(*) AS fk_count
                FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_schema = 'raw_toronto'
            """
            )
            result = conn.execute(count_sql)
            fk_count = result.fetchone()[0]
            print(f"\nFinal FK count in raw_toronto: {fk_count}")

        print("\n✓ Migration completed successfully")
        return 0

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
