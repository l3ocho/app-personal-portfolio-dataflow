"""Database loaders for Toronto housing data."""

from .amenities import load_amenities, load_amenity_counts
from .base import bulk_insert, get_session, upsert_by_key
from .census import load_census_data
from .cmhc import (
    ensure_toronto_cma_zone,
    load_cmhc_record,
    load_cmhc_rentals,
    load_excel_rental_data,
    load_statcan_cmhc_data,
    update_universe_from_excel,
)
from .cmhc_crosswalk import (
    build_cmhc_neighbourhood_crosswalk,
    disaggregate_zone_value,
    get_neighbourhood_weights_for_zone,
)
from .crime import load_crime_data
from .profile_loader import load_profile_data
from .dimensions import (
    generate_date_key,
    load_cmhc_zones,
    load_neighbourhoods,
    load_policy_events,
    load_time_dimension,
)

__all__ = [
    # Base utilities
    "get_session",
    "bulk_insert",
    "upsert_by_key",
    # Dimension loaders
    "generate_date_key",
    "load_time_dimension",
    "load_cmhc_zones",
    "load_neighbourhoods",
    "load_policy_events",
    # Fact loaders
    "load_cmhc_rentals",
    "load_cmhc_record",
    "load_excel_rental_data",
    "load_statcan_cmhc_data",
    "update_universe_from_excel",
    "ensure_toronto_cma_zone",
    # Phase 3 loaders
    "load_census_data",
    "load_crime_data",
    "load_amenities",
    "load_amenity_counts",
    "load_profile_data",
    # CMHC crosswalk
    "build_cmhc_neighbourhood_crosswalk",
    "get_neighbourhood_weights_for_zone",
    "disaggregate_zone_value",
]
