#!/usr/bin/env python3
"""Clean up deprecated mart tables from previous consolidations.

This script drops old mart tables that were consolidated into other tables:
- mart_neighbourhood_foundation (removed Sprint 13)
- mart_neighbourhood_demographics (→ mart_neighbourhood_people)
- mart_neighbourhood_amenities (→ mart_neighbourhood_people)
- mart_toronto_rentals (removed)
- mart_neighbourhood_housing_rentals (→ mart_neighbourhood_housing)

Used by: make dbt-run, make cleanup-deprecated-marts
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from dataflow.toronto.loaders import get_session  # noqa: E402

DEPRECATED_TABLES = [
    "mart_neighbourhood_foundation",
    "mart_neighbourhood_demographics",
    "mart_neighbourhood_amenities",
    "mart_toronto_rentals",
    "mart_neighbourhood_housing_rentals",
]


def cleanup_deprecated_marts() -> None:
    """Drop deprecated mart tables from mart_toronto schema."""
    try:
        with get_session() as session:
            for table_name in DEPRECATED_TABLES:
                try:
                    session.execute(
                        text(f"DROP TABLE IF EXISTS mart_toronto.{table_name} CASCADE")
                    )
                    session.commit()
                    print(f"✅ Dropped deprecated table: {table_name}")
                except Exception as e:
                    print(f"⚠️  Could not drop {table_name}: {e}")
                    session.rollback()
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cleanup_deprecated_marts()
    print("\n✅ Cleanup complete")
