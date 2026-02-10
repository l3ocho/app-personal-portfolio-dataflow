"""Pydantic schemas for Toronto neighbourhood data.

Includes schemas for neighbourhood boundaries, census profiles, and crime statistics.
"""

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CrimeType(str, Enum):
    """Major crime indicator types from Toronto Police data."""

    ASSAULT = "assault"
    AUTO_THEFT = "auto_theft"
    BREAK_AND_ENTER = "break_and_enter"
    HOMICIDE = "homicide"
    ROBBERY = "robbery"
    SHOOTING = "shooting"
    THEFT_OVER = "theft_over"
    THEFT_FROM_MOTOR_VEHICLE = "theft_from_motor_vehicle"
    OTHER = "other"


class NeighbourhoodRecord(BaseModel):
    """Schema for Toronto neighbourhood boundary data.

    Based on City of Toronto's 158 neighbourhoods dataset.
    AREA_ID maps to neighbourhood_id for consistency with police data (Hood_ID).
    """

    area_id: int = Field(description="AREA_ID from Toronto Open Data (1-158)")
    area_name: str = Field(max_length=100, description="Official neighbourhood name")
    area_short_code: str | None = Field(
        default=None, max_length=10, description="Short code (e.g., 'E01')"
    )
    geometry: dict[str, Any] | None = Field(
        default=None, description="GeoJSON geometry object"
    )

    model_config = {"str_strip_whitespace": True}


class CensusRecord(BaseModel):
    """Census profile data for a neighbourhood.

    Contains demographic and socioeconomic indicators from Statistics Canada
    census data, aggregated to the neighbourhood level.
    """

    neighbourhood_id: int = Field(
        ge=1, le=200, description="Neighbourhood ID (AREA_ID)"
    )
    census_year: int = Field(ge=2016, le=2030, description="Census year")
    population: int | None = Field(default=None, ge=0, description="Total population")
    population_density: Decimal | None = Field(
        default=None, ge=0, description="Population per square kilometre"
    )
    median_household_income: Decimal | None = Field(
        default=None, ge=0, description="Median household income (CAD)"
    )
    average_household_income: Decimal | None = Field(
        default=None, ge=0, description="Average household income (CAD)"
    )
    unemployment_rate: Decimal | None = Field(
        default=None, ge=0, le=100, description="Unemployment rate percentage"
    )
    pct_bachelors_or_higher: Decimal | None = Field(
        default=None, ge=0, le=100, description="Percentage with bachelor's degree+"
    )
    pct_owner_occupied: Decimal | None = Field(
        default=None, ge=0, le=100, description="Percentage owner-occupied dwellings"
    )
    pct_renter_occupied: Decimal | None = Field(
        default=None, ge=0, le=100, description="Percentage renter-occupied dwellings"
    )
    median_age: Decimal | None = Field(
        default=None, ge=0, le=120, description="Median age of residents"
    )
    average_dwelling_value: Decimal | None = Field(
        default=None, ge=0, description="Average dwelling value (CAD)"
    )

    model_config = {"str_strip_whitespace": True}


class CrimeRecord(BaseModel):
    """Crime statistics for a neighbourhood.

    Based on Toronto Police neighbourhood crime rates data.
    Hood_ID in source data maps to neighbourhood_id (AREA_ID).
    """

    neighbourhood_id: int = Field(
        ge=1, le=200, description="Neighbourhood ID (Hood_ID -> AREA_ID)"
    )
    year: int = Field(ge=2014, le=2030, description="Year of crime statistics")
    crime_type: CrimeType = Field(description="Type of crime (MCI category)")
    count: int = Field(ge=0, description="Number of incidents")
    rate_per_100k: Decimal | None = Field(
        default=None, ge=0, description="Rate per 100,000 population"
    )

    model_config = {"str_strip_whitespace": True}
