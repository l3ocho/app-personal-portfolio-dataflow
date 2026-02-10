"""Pydantic schemas for Toronto amenities data.

Includes schemas for parks, schools, childcare centres, and transit stops.
"""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class AmenityType(StrEnum):
    """Types of amenities tracked in the neighbourhood dashboard."""

    PARK = "park"
    SCHOOL = "school"
    CHILDCARE = "childcare"
    TRANSIT_STOP = "transit_stop"
    LIBRARY = "library"
    COMMUNITY_CENTRE = "community_centre"
    HOSPITAL = "hospital"


class AmenityRecord(BaseModel):
    """Amenity location record for a neighbourhood.

    Represents a single amenity (park, school, etc.) with its location
    and associated neighbourhood.
    """

    neighbourhood_id: int = Field(
        ge=1, le=200, description="Neighbourhood ID containing this amenity"
    )
    amenity_type: AmenityType = Field(description="Type of amenity")
    amenity_name: str = Field(max_length=200, description="Name of the amenity")
    address: str | None = Field(
        default=None, max_length=300, description="Street address"
    )
    latitude: Decimal | None = Field(
        default=None, ge=-90, le=90, description="Latitude (WGS84)"
    )
    longitude: Decimal | None = Field(
        default=None, ge=-180, le=180, description="Longitude (WGS84)"
    )

    model_config = {"str_strip_whitespace": True}


class AmenityCount(BaseModel):
    """Aggregated amenity count for a neighbourhood.

    Used for dashboard metrics showing amenity density per neighbourhood.
    """

    neighbourhood_id: int = Field(ge=1, le=200, description="Neighbourhood ID")
    amenity_type: AmenityType = Field(description="Type of amenity")
    count: int = Field(ge=0, description="Number of amenities of this type")
    year: int = Field(ge=2020, le=2030, description="Year of data snapshot")

    model_config = {"str_strip_whitespace": True}
