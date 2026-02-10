"""Service layer for generating GeoJSON from PostGIS geometry."""

import json
from functools import lru_cache
from typing import Any

import pandas as pd
from sqlalchemy import text

from portfolio_app.toronto.models import get_engine


def _execute_query(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


@lru_cache(maxsize=8)
def get_neighbourhoods_geojson(year: int = 2021) -> dict[str, Any]:
    """Get GeoJSON FeatureCollection for all neighbourhoods.

    Queries mart_neighbourhood_overview for geometries and basic properties.

    Args:
        year: Year to query for joining properties.

    Returns:
        GeoJSON FeatureCollection dictionary.
    """
    # Query geometries with ST_AsGeoJSON
    sql = """
        SELECT
            neighbourhood_id,
            neighbourhood_name,
            ST_AsGeoJSON(geometry)::json as geom,
            population,
            livability_score
        FROM mart_toronto.mart_neighbourhood_overview
        WHERE year = :year
          AND geometry IS NOT NULL
    """

    try:
        df = _execute_query(sql, {"year": year})
    except Exception:
        # Table might not exist or have data yet
        return _empty_geojson()

    if df.empty:
        return _empty_geojson()

    # Build GeoJSON features
    features = []
    for _, row in df.iterrows():
        geom = row["geom"]
        if geom is None:
            continue

        # Handle geometry that might be a string or dict
        if isinstance(geom, str):
            geom = json.loads(geom)

        feature = {
            "type": "Feature",
            "id": row["neighbourhood_id"],
            "properties": {
                "neighbourhood_id": int(row["neighbourhood_id"]),
                "neighbourhood_name": row["neighbourhood_name"],
                "population": int(row["population"])
                if pd.notna(row["population"])
                else None,
                "livability_score": float(row["livability_score"])
                if pd.notna(row["livability_score"])
                else None,
            },
            "geometry": geom,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


@lru_cache(maxsize=4)
def get_cmhc_zones_geojson() -> dict[str, Any]:
    """Get GeoJSON FeatureCollection for CMHC zones.

    Queries dim_cmhc_zone for zone geometries.

    Returns:
        GeoJSON FeatureCollection dictionary.
    """
    sql = """
        SELECT
            zone_code,
            zone_name,
            ST_AsGeoJSON(geometry)::json as geom
        FROM raw_toronto.dim_cmhc_zone
        WHERE geometry IS NOT NULL
    """

    try:
        df = _execute_query(sql, {})
    except Exception:
        return _empty_geojson()

    if df.empty:
        return _empty_geojson()

    features = []
    for _, row in df.iterrows():
        geom = row["geom"]
        if geom is None:
            continue

        if isinstance(geom, str):
            geom = json.loads(geom)

        feature = {
            "type": "Feature",
            "id": row["zone_code"],
            "properties": {
                "zone_code": row["zone_code"],
                "zone_name": row["zone_name"],
            },
            "geometry": geom,
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_neighbourhood_geometry(neighbourhood_id: int) -> dict[str, Any] | None:
    """Get GeoJSON geometry for a single neighbourhood.

    Args:
        neighbourhood_id: The neighbourhood ID.

    Returns:
        GeoJSON geometry dict, or None if not found.
    """
    sql = """
        SELECT ST_AsGeoJSON(geometry)::json as geom
        FROM raw_toronto.dim_neighbourhood
        WHERE neighbourhood_id = :neighbourhood_id
          AND geometry IS NOT NULL
    """

    try:
        df = _execute_query(sql, {"neighbourhood_id": neighbourhood_id})
    except Exception:
        return None

    if df.empty:
        return None

    geom = df.iloc[0]["geom"]
    if isinstance(geom, str):
        result: dict[str, Any] = json.loads(geom)
        return result
    return dict(geom) if geom is not None else None


def _empty_geojson() -> dict[str, Any]:
    """Return an empty GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": [],
    }
