"""Service layer for querying neighbourhood data from dbt marts."""

import logging
from functools import lru_cache
from typing import Any

import pandas as pd
from sqlalchemy import text

from portfolio_app.toronto.models import get_engine

logger = logging.getLogger(__name__)


def _execute_query(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame.

    Args:
        sql: SQL query string.
        params: Query parameters.

    Returns:
        pandas DataFrame with results, or empty DataFrame on error.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        logger.debug(f"Failed SQL: {sql}")
        logger.debug(f"Params: {params}")
        return pd.DataFrame()


def get_overview_data(year: int = 2021) -> pd.DataFrame:
    """Get overview data for all neighbourhoods.

    Queries mart_neighbourhood_overview for livability scores and components.

    Args:
        year: Census year to query.

    Returns:
        DataFrame with columns: neighbourhood_id, neighbourhood_name,
        livability_score, safety_score, affordability_score, amenity_score,
        population, median_household_income, etc.
    """
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            year,
            population,
            median_household_income,
            livability_score,
            safety_score,
            affordability_score,
            amenity_score,
            crime_rate_per_100k,
            rent_to_income_pct,
            avg_rent_2bed,
            total_amenities_per_1000
        FROM mart_toronto.mart_neighbourhood_overview
        WHERE year = :year
        ORDER BY livability_score DESC NULLS LAST
    """
    return _execute_query(sql, {"year": year})


def get_housing_data(year: int = 2021) -> pd.DataFrame:
    """Get housing data for all neighbourhoods.

    Queries mart_neighbourhood_housing for affordability metrics.

    Args:
        year: Year to query.

    Returns:
        DataFrame with columns: neighbourhood_id, neighbourhood_name,
        avg_rent_2bed, vacancy_rate, rent_to_income_pct, affordability_index, etc.
    """
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            year,
            pct_owner_occupied,
            pct_renter_occupied,
            average_dwelling_value,
            median_household_income,
            avg_rent_bachelor,
            avg_rent_1bed,
            avg_rent_2bed,
            avg_rent_3bed,
            vacancy_rate,
            total_rental_units,
            rent_to_income_pct,
            is_affordable,
            affordability_index,
            rent_yoy_change_pct,
            income_quintile
        FROM mart_toronto.mart_neighbourhood_housing
        WHERE year = :year
        ORDER BY affordability_index ASC NULLS LAST
    """
    return _execute_query(sql, {"year": year})


def get_safety_data(year: int = 2021) -> pd.DataFrame:
    """Get safety/crime data for all neighbourhoods.

    Queries mart_neighbourhood_safety for crime statistics.

    Args:
        year: Year to query.

    Returns:
        DataFrame with columns: neighbourhood_id, neighbourhood_name,
        total_crime_rate, violent_crimes, property_crimes, etc.
    """
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            year,
            total_incidents as total_crimes,
            crime_rate_per_100k as total_crime_rate,
            COALESCE(assault_count, 0) + COALESCE(robbery_count, 0) + COALESCE(homicide_count, 0) as violent_crimes,
            COALESCE(break_enter_count, 0) + COALESCE(auto_theft_count, 0) as property_crimes,
            COALESCE(theft_over_count, 0) as theft_crimes,
            crime_yoy_change_pct
        FROM mart_toronto.mart_neighbourhood_safety
        WHERE year = :year
        ORDER BY crime_rate_per_100k ASC NULLS LAST
    """
    return _execute_query(sql, {"year": year})


def get_demographics_data(year: int = 2021) -> pd.DataFrame:
    """Get demographic data for all neighbourhoods.

    Queries mart_neighbourhood_demographics for population/income metrics.

    Args:
        year: Census year to query.

    Returns:
        DataFrame with columns: neighbourhood_id, neighbourhood_name,
        population, median_age, median_income, diversity_index, etc.
    """
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            year,
            population,
            population_density,
            median_household_income,
            average_household_income,
            income_quintile,
            income_index,
            median_age,
            age_index,
            pct_owner_occupied,
            pct_renter_occupied,
            education_bachelors_pct as pct_bachelors_or_higher,
            unemployment_rate,
            tenure_diversity_index as diversity_index
        FROM mart_toronto.mart_neighbourhood_demographics
        WHERE year = :year
        ORDER BY population DESC NULLS LAST
    """
    return _execute_query(sql, {"year": year})


def get_latest_amenities_year() -> int:
    """Get the latest available year for amenities data.

    Returns:
        Latest year available in amenities table.
    """
    sql = """
        SELECT MAX(year) as latest_year
        FROM mart_toronto.mart_neighbourhood_amenities
    """
    df = _execute_query(sql)
    if df.empty or df["latest_year"].isna().all():
        return 2024  # fallback
    return int(df["latest_year"].iloc[0])


def get_amenities_data(year: int | None = None) -> pd.DataFrame:
    """Get amenities data for all neighbourhoods.

    Queries mart_neighbourhood_amenities for parks, schools, transit.
    Automatically uses the latest available year regardless of year parameter.

    Args:
        year: Ignored. Always uses latest available year.

    Returns:
        DataFrame with columns: neighbourhood_id, neighbourhood_name,
        amenity_score, parks_per_1000, schools_per_1000, etc.
    """
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            year,
            parks_count as park_count,
            parks_per_1000,
            schools_count as school_count,
            schools_per_1000,
            childcare_count,
            transit_count,
            transit_per_1000,
            total_amenities,
            total_amenities_per_1000,
            amenity_index as amenity_score,
            amenity_tier as amenity_rank
        FROM mart_toronto.mart_neighbourhood_amenities
        WHERE year = (SELECT MAX(year) FROM mart_toronto.mart_neighbourhood_amenities)
        ORDER BY amenity_index DESC NULLS LAST
    """
    return _execute_query(sql)


def get_neighbourhood_details(
    neighbourhood_id: int, year: int = 2021
) -> dict[str, Any]:
    """Get detailed data for a single neighbourhood.

    Combines data from all mart tables for a complete neighbourhood profile.

    Args:
        neighbourhood_id: The neighbourhood ID.
        year: Year to query.

    Returns:
        Dictionary with all metrics for the neighbourhood.
    """
    sql = """
        SELECT
            o.neighbourhood_id,
            o.neighbourhood_name,
            o.year,
            o.population,
            o.median_household_income,
            o.livability_score,
            o.safety_score,
            o.affordability_score,
            o.amenity_score,
            s.total_incidents as total_crimes,
            s.crime_rate_per_100k,
            COALESCE(s.assault_count, 0) + COALESCE(s.robbery_count, 0) + COALESCE(s.homicide_count, 0) as violent_crime_rate,
            COALESCE(s.break_enter_count, 0) + COALESCE(s.auto_theft_count, 0) as property_crime_rate,
            h.avg_rent_2bed,
            h.vacancy_rate,
            h.rent_to_income_pct,
            h.affordability_index,
            h.pct_owner_occupied,
            h.pct_renter_occupied,
            d.median_age,
            d.tenure_diversity_index as diversity_index,
            d.unemployment_rate,
            d.pct_bachelors_or_higher,
            a.parks_count as park_count,
            a.schools_count as school_count,
            a.total_amenities
        FROM mart_toronto.mart_neighbourhood_overview o
        LEFT JOIN mart_toronto.mart_neighbourhood_safety s
            ON o.neighbourhood_id = s.neighbourhood_id
            AND o.year = s.year
        LEFT JOIN mart_toronto.mart_neighbourhood_housing h
            ON o.neighbourhood_id = h.neighbourhood_id
            AND o.year = h.year
        LEFT JOIN mart_toronto.mart_neighbourhood_demographics d
            ON o.neighbourhood_id = d.neighbourhood_id
            AND o.year = d.year
        LEFT JOIN mart_toronto.mart_neighbourhood_amenities a
            ON o.neighbourhood_id = a.neighbourhood_id
            AND o.year = a.year
        WHERE o.neighbourhood_id = :neighbourhood_id
          AND o.year = :year
    """
    df = _execute_query(sql, {"neighbourhood_id": neighbourhood_id, "year": year})

    if df.empty:
        return {}

    return {str(k): v for k, v in df.iloc[0].to_dict().items()}


@lru_cache(maxsize=32)
def get_neighbourhood_list(year: int = 2021) -> list[dict[str, Any]]:
    """Get list of all neighbourhoods for dropdown selectors.

    Args:
        year: Year to query.

    Returns:
        List of dicts with neighbourhood_id, name, and population.
    """
    sql = """
        SELECT DISTINCT
            neighbourhood_id,
            neighbourhood_name,
            population
        FROM mart_toronto.mart_neighbourhood_overview
        WHERE year = :year
        ORDER BY neighbourhood_name
    """
    df = _execute_query(sql, {"year": year})
    if df.empty:
        return []
    return list(df.to_dict("records"))  # type: ignore[arg-type]


def get_rankings(
    metric: str,
    year: int = 2021,
    top_n: int = 10,
    ascending: bool = True,
) -> pd.DataFrame:
    """Get top/bottom neighbourhoods for a specific metric.

    Args:
        metric: Column name to rank by.
        year: Year to query.
        top_n: Number of top and bottom records.
        ascending: If True, rank from lowest to highest (good for crime, rent).

    Returns:
        DataFrame with top and bottom neighbourhoods.
    """
    # Map metrics to their source tables
    table_map = {
        "livability_score": "mart_toronto.mart_neighbourhood_overview",
        "safety_score": "mart_toronto.mart_neighbourhood_overview",
        "affordability_score": "mart_toronto.mart_neighbourhood_overview",
        "amenity_score": "mart_toronto.mart_neighbourhood_overview",
        "crime_rate_per_100k": "mart_toronto.mart_neighbourhood_safety",
        "total_crime_rate": "mart_toronto.mart_neighbourhood_safety",
        "avg_rent_2bed": "mart_toronto.mart_neighbourhood_housing",
        "affordability_index": "mart_toronto.mart_neighbourhood_housing",
        "population": "mart_toronto.mart_neighbourhood_demographics",
        "median_household_income": "mart_toronto.mart_neighbourhood_demographics",
    }

    table = table_map.get(metric, "mart_toronto.mart_neighbourhood_overview")
    year_col = "census_year" if "demographics" in table else "year"

    order = "ASC" if ascending else "DESC"
    reverse_order = "DESC" if ascending else "ASC"

    sql = f"""
        (
            SELECT neighbourhood_id, neighbourhood_name, {metric}, 'bottom' as rank_group
            FROM {table}
            WHERE {year_col} = :year AND {metric} IS NOT NULL
            ORDER BY {metric} {order}
            LIMIT :top_n
        )
        UNION ALL
        (
            SELECT neighbourhood_id, neighbourhood_name, {metric}, 'top' as rank_group
            FROM {table}
            WHERE {year_col} = :year AND {metric} IS NOT NULL
            ORDER BY {metric} {reverse_order}
            LIMIT :top_n
        )
    """
    return _execute_query(sql, {"year": year, "top_n": top_n})


def get_city_averages(year: int = 2021) -> dict[str, Any]:
    """Get city-wide average metrics.

    Args:
        year: Year to query.

    Returns:
        Dictionary with city averages for key metrics.
    """
    sql = """
        SELECT
            AVG(livability_score) as avg_livability_score,
            AVG(safety_score) as avg_safety_score,
            AVG(affordability_score) as avg_affordability_score,
            AVG(amenity_score) as avg_amenity_score,
            SUM(population) as total_population,
            AVG(median_household_income) as avg_median_income,
            AVG(crime_rate_per_100k) as avg_crime_rate,
            AVG(avg_rent_2bed) as avg_rent_2bed,
            AVG(rent_to_income_pct) as avg_rent_to_income
        FROM mart_toronto.mart_neighbourhood_overview
        WHERE year = :year
    """
    df = _execute_query(sql, {"year": year})

    if df.empty:
        return {}

    result: dict[str, Any] = {str(k): v for k, v in df.iloc[0].to_dict().items()}
    # Round numeric values
    for key, value in result.items():
        if pd.notna(value) and isinstance(value, float):
            result[key] = round(value, 2)

    return result
