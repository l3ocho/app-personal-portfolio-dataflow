"""Pydantic schemas for CMHC rental market data."""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class BedroomType(StrEnum):
    """CMHC bedroom type categories."""

    BACHELOR = "Bachelor"
    ONE_BED = "1 Bedroom"
    TWO_BED = "2 Bedroom"
    THREE_BED_PLUS = "3 Bedroom+"
    TOTAL = "Total"


class ReliabilityCode(StrEnum):
    """CMHC data reliability codes.

    Based on coefficient of variation (CV).
    """

    EXCELLENT = "a"  # CV <= 2.5%
    GOOD = "b"  # 2.5% < CV <= 5%
    FAIR = "c"  # 5% < CV <= 10%
    POOR = "d"  # CV > 10%
    SUPPRESSED = "**"  # Sample too small


class CMHCRentalRecord(BaseModel):
    """Schema for a single CMHC rental survey record.

    Represents rental data for one zone and bedroom type in one survey year.
    """

    survey_year: int = Field(ge=1990, description="Survey year (October snapshot)")
    zone_code: str = Field(max_length=10, description="CMHC zone identifier")
    zone_name: str = Field(max_length=100, description="Zone name")
    bedroom_type: BedroomType = Field(description="Bedroom category")
    universe: int | None = Field(
        default=None, ge=0, description="Total rental units in zone"
    )
    vacancy_rate: Decimal | None = Field(
        default=None, ge=0, le=100, description="Vacancy rate (%)"
    )
    vacancy_rate_reliability: ReliabilityCode | None = Field(default=None)
    average_rent: Decimal | None = Field(
        default=None, ge=0, description="Average monthly rent ($)"
    )
    average_rent_reliability: ReliabilityCode | None = Field(default=None)
    rent_change_pct: Decimal | None = Field(
        default=None, description="YoY rent change (%)"
    )
    turnover_rate: Decimal | None = Field(
        default=None, ge=0, le=100, description="Unit turnover rate (%)"
    )

    model_config = {"str_strip_whitespace": True}


class CMHCAnnualSurvey(BaseModel):
    """Schema for a complete CMHC annual survey for Toronto.

    Contains all zone and bedroom type combinations for one survey year.
    """

    survey_year: int
    records: list[CMHCRentalRecord]

    @property
    def zone_count(self) -> int:
        """Number of unique zones in survey."""
        return len({r.zone_code for r in self.records})
