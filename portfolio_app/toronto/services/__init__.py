"""Data service layer for Toronto neighbourhood dashboard."""

from .geometry_service import (
    get_cmhc_zones_geojson,
    get_neighbourhoods_geojson,
)
from .neighbourhood_service import (
    get_amenities_data,
    get_city_averages,
    get_demographics_data,
    get_housing_data,
    get_neighbourhood_details,
    get_neighbourhood_list,
    get_overview_data,
    get_rankings,
    get_safety_data,
)

__all__ = [
    # Neighbourhood data
    "get_overview_data",
    "get_housing_data",
    "get_safety_data",
    "get_demographics_data",
    "get_amenities_data",
    "get_neighbourhood_details",
    "get_neighbourhood_list",
    "get_rankings",
    "get_city_averages",
    # Geometry
    "get_neighbourhoods_geojson",
    "get_cmhc_zones_geojson",
]
