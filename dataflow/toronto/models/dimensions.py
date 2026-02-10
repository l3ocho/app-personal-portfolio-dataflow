"""SQLAlchemy models for dimension tables."""

from datetime import date

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

# Schema constants
RAW_TORONTO_SCHEMA = "raw_toronto"


class DimTime(Base):
    """Time dimension table (shared across all projects).

    Note: Stays in public schema as it's a shared dimension.
    """

    __tablename__ = "dim_time"
    __table_args__ = {"schema": "public"}

    date_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    month_name: Mapped[str] = mapped_column(String(20), nullable=False)
    is_month_start: Mapped[bool] = mapped_column(Boolean, default=True)


class DimCMHCZone(Base):
    """CMHC zone dimension table with PostGIS geometry."""

    __tablename__ = "dim_cmhc_zone"
    __table_args__ = {"schema": RAW_TORONTO_SCHEMA}

    zone_key: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    zone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)


class DimNeighbourhood(Base):
    """City of Toronto neighbourhood dimension.

    Note: No FK to fact tables in V1 - reference overlay only.
    """

    __tablename__ = "dim_neighbourhood"
    __table_args__ = {"schema": RAW_TORONTO_SCHEMA}

    neighbourhood_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    geometry = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    land_area_sqkm: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    pop_density_per_sqkm: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    pct_bachelors_or_higher: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    median_household_income: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    pct_owner_occupied: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pct_renter_occupied: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    census_year: Mapped[int] = mapped_column(Integer, default=2021)


class DimPolicyEvent(Base):
    """Policy event dimension for time-series annotation."""

    __tablename__ = "dim_policy_event"
    __table_args__ = {"schema": RAW_TORONTO_SCHEMA}

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    level: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # federal/provincial/municipal
    category: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # monetary/tax/regulatory/supply/economic
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_direction: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # bearish/bullish/neutral
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[str] = mapped_column(
        String(10), default="medium"
    )  # high/medium/low
