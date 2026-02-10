"""Pydantic schemas for dimension tables."""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class PolicyLevel(str, Enum):
    """Government level for policy events."""

    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"


class PolicyCategory(str, Enum):
    """Policy event category."""

    MONETARY = "monetary"
    TAX = "tax"
    REGULATORY = "regulatory"
    SUPPLY = "supply"
    ECONOMIC = "economic"


class ExpectedDirection(str, Enum):
    """Expected price impact direction."""

    BULLISH = "bullish"  # Expected to increase prices
    BEARISH = "bearish"  # Expected to decrease prices
    NEUTRAL = "neutral"  # Uncertain or mixed impact


class Confidence(str, Enum):
    """Confidence level in policy event data."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TimeDimension(BaseModel):
    """Schema for time dimension record."""

    date_key: int = Field(description="Date key in YYYYMMDD format")
    full_date: date
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    quarter: int = Field(ge=1, le=4)
    month_name: str = Field(max_length=20)
    is_month_start: bool = True


class CMHCZone(BaseModel):
    """Schema for CMHC zone dimension."""

    zone_code: str = Field(max_length=10)
    zone_name: str = Field(max_length=100)
    geometry_wkt: str | None = Field(default=None, description="WKT geometry string")


class Neighbourhood(BaseModel):
    """Schema for City of Toronto neighbourhood dimension.

    Note: No FK to fact tables in V1 - reference overlay only.
    """

    neighbourhood_id: int = Field(ge=1, le=200)
    name: str = Field(max_length=100)
    geometry_wkt: str | None = Field(default=None)
    population: int | None = Field(default=None, ge=0)
    land_area_sqkm: Decimal | None = Field(default=None, ge=0)
    pop_density_per_sqkm: Decimal | None = Field(default=None, ge=0)
    pct_bachelors_or_higher: Decimal | None = Field(default=None, ge=0, le=100)
    median_household_income: Decimal | None = Field(default=None, ge=0)
    pct_owner_occupied: Decimal | None = Field(default=None, ge=0, le=100)
    pct_renter_occupied: Decimal | None = Field(default=None, ge=0, le=100)
    census_year: int = Field(default=2021, description="Census year for SCD tracking")


class PolicyEvent(BaseModel):
    """Schema for policy event dimension.

    Used for time-series annotation. No causation claims.
    """

    event_date: date = Field(description="Date event was announced/occurred")
    effective_date: date | None = Field(
        default=None, description="Date policy took effect"
    )
    level: PolicyLevel
    category: PolicyCategory
    title: str = Field(max_length=200, description="Short event title for display")
    description: str | None = Field(
        default=None, description="Longer description for tooltip"
    )
    expected_direction: ExpectedDirection
    source_url: HttpUrl | None = Field(default=None)
    confidence: Confidence = Field(default=Confidence.MEDIUM)

    model_config = {"str_strip_whitespace": True}
