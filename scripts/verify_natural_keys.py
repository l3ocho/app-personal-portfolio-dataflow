#!/usr/bin/env python3
"""Verify natural key uniqueness for composite constraints."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

queries = {
    "fact_census": """
        SELECT neighbourhood_id, census_year, COUNT(*) as cnt
        FROM raw_toronto.fact_census
        GROUP BY neighbourhood_id, census_year
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC, neighbourhood_id, census_year;
    """,
    "fact_crime": """
        SELECT neighbourhood_id, year, crime_type, COUNT(*) as cnt
        FROM raw_toronto.fact_crime
        GROUP BY neighbourhood_id, year, crime_type
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC, neighbourhood_id, year, crime_type;
    """,
    "fact_amenities": """
        SELECT neighbourhood_id, amenity_type, year, COUNT(*) as cnt
        FROM raw_toronto.fact_amenities
        GROUP BY neighbourhood_id, amenity_type, year
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC, neighbourhood_id, amenity_type, year;
    """,
    "bridge_cmhc_neighbourhood": """
        SELECT cmhc_zone_code, neighbourhood_id, COUNT(*) as cnt
        FROM raw_toronto.bridge_cmhc_neighbourhood
        GROUP BY cmhc_zone_code, neighbourhood_id
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC, cmhc_zone_code, neighbourhood_id;
    """,
}

print("=" * 80)
print("NATURAL KEY UNIQUENESS VERIFICATION")
print("=" * 80)
print()

with engine.connect() as conn:
    for table_name, query in queries.items():
        print(f"Table: {table_name}")
        print("-" * 80)

        result = conn.execute(text(query))
        rows = result.fetchall()

        if rows:
            print(f"⚠️  DUPLICATES FOUND: {len(rows)} combinations have duplicates")
            print()
            print("Sample duplicates (first 10):")
            for i, row in enumerate(rows[:10], 1):
                print(f"  {i}. {dict(row._mapping)}")
            if len(rows) > 10:
                print(f"  ... and {len(rows) - 10} more")
        else:
            print("✓ No duplicates found - natural key is unique")

        print()
        print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)

# Run summary counts
with engine.connect() as conn:
    for table_name in queries:
        schema, table = (
            table_name.split("_", 1)
            if "_" in table_name
            else ("raw_toronto", table_name)
        )
        full_table = f"raw_toronto.{table_name}"

        count_query = f"SELECT COUNT(*) FROM {full_table};"
        total_rows = conn.execute(text(count_query)).scalar()
        print(f"{table_name}: {total_rows} total rows")
