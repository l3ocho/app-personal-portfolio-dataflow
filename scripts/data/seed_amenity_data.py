#!/usr/bin/env python3
"""Seed sample data for development/testing.

This script:
- Populates fact_amenities with sample data
- Updates dim_neighbourhood with population from fact_census
- Seeds median_age in fact_census where missing
- Seeds census housing columns (tenure, income, dwelling value)
- Seeds housing mart data (rent, affordability)
- Seeds overview mart data (safety_score, population)
- Runs dbt to rebuild the marts

Usage:
    python scripts/data/seed_amenity_data.py

Run this after load_toronto_data.py to ensure notebooks have data.
"""

import os
import random
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)


def seed_amenities() -> int:
    """Insert sample amenity data for all neighbourhoods."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT neighbourhood_id FROM raw_toronto.dim_neighbourhood")
        )
        neighbourhood_ids = [row[0] for row in result]

    print(f"Found {len(neighbourhood_ids)} neighbourhoods")

    amenity_types = [
        "Parks",
        "Schools",
        "Transit Stops",
        "Libraries",
        "Community Centres",
        "Recreation",
    ]
    year = 2024

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM public.fact_amenities"))

        total = 0
        for n_id in neighbourhood_ids:
            for amenity_type in amenity_types:
                count = random.randint(1, 50)
                conn.execute(
                    text(
                        """
                    INSERT INTO public.fact_amenities
                    (neighbourhood_id, amenity_type, count, year)
                    VALUES (:neighbourhood_id, :amenity_type, :count, :year)
                """
                    ),
                    {
                        "neighbourhood_id": n_id,
                        "amenity_type": amenity_type,
                        "count": count,
                        "year": year,
                    },
                )
                total += 1

    print(f"Inserted {total} amenity records")
    return total


def update_population() -> int:
    """Update dim_neighbourhood with population from fact_census."""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
            UPDATE raw_toronto.dim_neighbourhood dn
            SET population = fc.population
            FROM public.fact_census fc
            WHERE dn.neighbourhood_id = fc.neighbourhood_id
              AND fc.census_year = 2021
        """
            )
        )
        count = int(result.rowcount)

    print(f"Updated {count} neighbourhoods with population")
    return count


def seed_median_age() -> int:
    """Seed median_age in fact_census where missing."""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT id FROM public.fact_census WHERE median_age IS NULL")
        )
        null_ids = [row[0] for row in result]

        if not null_ids:
            print("No NULL median_age values found")
            return 0

        for census_id in null_ids:
            age = random.randint(30, 50)
            conn.execute(
                text("UPDATE public.fact_census SET median_age = :age WHERE id = :id"),
                {"age": age, "id": census_id},
            )

    print(f"Seeded median_age for {len(null_ids)} census records")
    return len(null_ids)


def seed_census_housing() -> int:
    """Seed housing columns in fact_census where missing."""
    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT id FROM public.fact_census WHERE pct_owner_occupied IS NULL")
        )
        null_ids = [row[0] for row in result]

        if not null_ids:
            print("No NULL census housing values found")
            return 0

        for census_id in null_ids:
            conn.execute(
                text(
                    """
                UPDATE public.fact_census SET
                    pct_owner_occupied = :owner,
                    pct_renter_occupied = :renter,
                    average_dwelling_value = :dwelling,
                    median_household_income = :income
                WHERE id = :id
            """
                ),
                {
                    "id": census_id,
                    "owner": round(random.uniform(30, 80), 1),
                    "renter": round(random.uniform(20, 70), 1),
                    "dwelling": random.randint(400000, 1500000),
                    "income": random.randint(50000, 180000),
                },
            )

    print(f"Seeded census housing data for {len(null_ids)} records")
    return len(null_ids)


def seed_housing_mart() -> int:
    """Seed housing mart with rental and affordability data for multiple years."""
    engine = create_engine(DATABASE_URL)
    total = 0

    # First update existing NULL records
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
            SELECT neighbourhood_id, year
            FROM mart_toronto.mart_neighbourhood_housing
            WHERE avg_rent_2bed IS NULL
        """
            )
        )
        rows = [dict(row._mapping) for row in result]

        for row in rows:
            avg_rent = random.randint(1800, 3200)
            income = random.randint(55000, 180000)
            rent_to_income = round((avg_rent * 12 / income) * 100, 2)
            affordability = round(rent_to_income / 30 * 100, 1)

            conn.execute(
                text(
                    """
                UPDATE mart_toronto.mart_neighbourhood_housing SET
                    avg_rent_bachelor = :bachelor,
                    avg_rent_1bed = :onebed,
                    avg_rent_2bed = :twobed,
                    avg_rent_3bed = :threebed,
                    vacancy_rate = :vacancy,
                    rent_to_income_pct = :rent_income,
                    affordability_index = :afford_idx,
                    is_affordable = :is_afford,
                    median_household_income = :income,
                    pct_owner_occupied = :owner,
                    pct_renter_occupied = :renter
                WHERE neighbourhood_id = :nid AND year = :year
            """
                ),
                {
                    "nid": row["neighbourhood_id"],
                    "year": row["year"],
                    "bachelor": avg_rent - 500,
                    "onebed": avg_rent - 300,
                    "twobed": avg_rent,
                    "threebed": avg_rent + 400,
                    "vacancy": round(random.uniform(0.5, 4.5), 1),
                    "rent_income": rent_to_income,
                    "afford_idx": affordability,
                    "is_afford": rent_to_income <= 30,
                    "income": income,
                    "owner": round(random.uniform(30, 75), 1),
                    "renter": round(random.uniform(25, 70), 1),
                },
            )
            total += 1

    # Then insert multi-year data for trend charts
    years = [2019, 2020, 2022, 2023, 2024]
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "SELECT neighbourhood_id, name, geometry FROM raw_toronto.dim_neighbourhood"
            )
        )
        neighbourhoods = [dict(row._mapping) for row in result]

        for n in neighbourhoods:
            for year in years:
                # Check if exists
                exists = conn.execute(
                    text(
                        """
                    SELECT 1 FROM mart_toronto.mart_neighbourhood_housing
                    WHERE neighbourhood_id = :nid AND year = :year
                """
                    ),
                    {"nid": n["neighbourhood_id"], "year": year},
                ).fetchone()

                if exists:
                    continue

                base_rent = random.randint(1800, 2800)
                year_factor = (year - 2019) * random.randint(50, 150)
                avg_rent = base_rent + year_factor
                income = random.randint(55000, 180000)
                rent_to_income = round((avg_rent * 12 / income) * 100, 2)

                conn.execute(
                    text(
                        """
                    INSERT INTO mart_toronto.mart_neighbourhood_housing
                    (neighbourhood_id, neighbourhood_name, geometry, year,
                     avg_rent_bachelor, avg_rent_1bed, avg_rent_2bed, avg_rent_3bed,
                     vacancy_rate, rent_to_income_pct, affordability_index, is_affordable,
                     median_household_income, pct_owner_occupied, pct_renter_occupied)
                    VALUES
                    (:nid, :name, :geom, :year,
                     :bachelor, :onebed, :twobed, :threebed,
                     :vacancy, :rent_income, :afford_idx, :is_afford,
                     :income, :owner, :renter)
                """
                    ),
                    {
                        "nid": n["neighbourhood_id"],
                        "name": n["name"],
                        "geom": n["geometry"],
                        "year": year,
                        "bachelor": avg_rent - 500,
                        "onebed": avg_rent - 300,
                        "twobed": avg_rent,
                        "threebed": avg_rent + 400,
                        "vacancy": round(random.uniform(0.5, 4.5), 1),
                        "rent_income": rent_to_income,
                        "afford_idx": round(rent_to_income / 30 * 100, 1),
                        "is_afford": rent_to_income <= 30,
                        "income": income,
                        "owner": round(random.uniform(30, 75), 1),
                        "renter": round(random.uniform(25, 70), 1),
                    },
                )
                total += 1

    print(f"Seeded housing mart data for {total} records")
    return total


def seed_overview_mart() -> int:
    """Seed overview mart with safety_score and population."""
    engine = create_engine(DATABASE_URL)
    total = 0

    with engine.begin() as conn:
        # Seed safety_score
        result = conn.execute(
            text(
                """
            SELECT neighbourhood_id, year
            FROM mart_toronto.mart_neighbourhood_overview
            WHERE safety_score IS NULL
        """
            )
        )
        rows = [dict(row._mapping) for row in result]

        for row in rows:
            conn.execute(
                text(
                    """
                UPDATE mart_toronto.mart_neighbourhood_overview
                SET safety_score = :score
                WHERE neighbourhood_id = :nid AND year = :year
            """
                ),
                {
                    "nid": row["neighbourhood_id"],
                    "year": row["year"],
                    "score": round(random.uniform(40, 95), 1),
                },
            )
            total += 1

        # Seed population
        result = conn.execute(
            text(
                """
            SELECT neighbourhood_id, year
            FROM mart_toronto.mart_neighbourhood_overview
            WHERE population IS NULL
        """
            )
        )
        rows = [dict(row._mapping) for row in result]

        for row in rows:
            conn.execute(
                text(
                    """
                UPDATE mart_toronto.mart_neighbourhood_overview
                SET population = :pop
                WHERE neighbourhood_id = :nid AND year = :year
            """
                ),
                {
                    "nid": row["neighbourhood_id"],
                    "year": row["year"],
                    "pop": random.randint(8000, 45000),
                },
            )
            total += 1

    print(f"Seeded overview mart data for {total} records")
    return total


def run_dbt() -> bool:
    """Run dbt to rebuild marts."""
    dbt_dir = PROJECT_ROOT / "dbt"
    venv_dbt = PROJECT_ROOT / ".venv" / "bin" / "dbt"
    dbt_cmd = str(venv_dbt) if venv_dbt.exists() else "dbt"

    print("Running dbt to rebuild marts...")

    env = os.environ.copy()
    env["POSTGRES_PASSWORD"] = os.environ.get("POSTGRES_PASSWORD", "")

    result = subprocess.run(
        [dbt_cmd, "run", "--profiles-dir", str(dbt_dir)],
        cwd=dbt_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    if result.returncode != 0:
        print(f"dbt failed:\n{result.stdout}\n{result.stderr}")
        return False

    print("dbt completed successfully")
    return True


def main() -> int:
    """Main entry point."""
    print("Seeding development data...")

    seed_amenities()
    update_population()
    seed_median_age()
    seed_census_housing()

    if not run_dbt():
        return 1

    # Seed mart tables after dbt rebuild
    seed_housing_mart()
    seed_overview_mart()

    print("\nDone! Development data is ready.")
    return 0


if __name__ == "__main__":
    result = main()
    sys.exit(result)
