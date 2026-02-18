"""SQLAlchemy models for fact tables."""

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .dimensions import RAW_TORONTO_SCHEMA


class BridgeCMHCNeighbourhood(Base):
    """Bridge table for CMHC zone to neighbourhood mapping with area weights.

    Enables disaggregation of CMHC zone-level rental data to neighbourhood level
    using area-based proportional weights computed via PostGIS.
    """

    __tablename__ = "bridge_cmhc_neighbourhood"
    __table_args__ = (
        Index("ix_bridge_cmhc_zone", "cmhc_zone_code"),
        Index("ix_bridge_neighbourhood", "neighbourhood_id"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cmhc_zone_code: Mapped[str] = mapped_column(String(10), nullable=False)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False
    )  # 0.0000 to 1.0000


class FactCensus(Base):
    """Census statistics by neighbourhood and year.

    Grain: One row per neighbourhood per census year.
    """

    __tablename__ = "fact_census"
    __table_args__ = (
        Index("ix_fact_census_neighbourhood_year", "neighbourhood_id", "census_year"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    census_year: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    population_density: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    median_household_income: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    average_household_income: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    unemployment_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pct_bachelors_or_higher: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pct_owner_occupied: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pct_renter_occupied: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    median_age: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    average_dwelling_value: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )


class FactCrime(Base):
    """Crime statistics by neighbourhood and year.

    Grain: One row per neighbourhood per year per crime type.
    """

    __tablename__ = "fact_crime"
    __table_args__ = (
        Index("ix_fact_crime_neighbourhood_year", "neighbourhood_id", "year"),
        Index("ix_fact_crime_type", "crime_type"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    crime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_per_100k: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)


class FactAmenities(Base):
    """Amenity counts by neighbourhood.

    Grain: One row per neighbourhood per amenity type per year.
    """

    __tablename__ = "fact_amenities"
    __table_args__ = (
        Index("ix_fact_amenities_neighbourhood_year", "neighbourhood_id", "year"),
        Index("ix_fact_amenities_type", "amenity_type"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amenity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)


class FactRentals(Base):
    """Fact table for CMHC rental market data.

    Grain: One row per zone per bedroom type per survey year.
    """

    __tablename__ = "fact_rentals"
    __table_args__ = {"schema": RAW_TORONTO_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date_key: Mapped[int] = mapped_column(
        Integer, ForeignKey("public.dim_time.date_key"), nullable=False
    )
    zone_key: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{RAW_TORONTO_SCHEMA}.dim_cmhc_zone.zone_key"),
        nullable=False,
    )
    bedroom_type: Mapped[str] = mapped_column(String(20), nullable=False)
    universe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_rent: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    vacancy_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    turnover_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rent_change_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    reliability_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # Relationships - explicit foreign_keys needed for cross-schema joins
    time = relationship("DimTime", foreign_keys=[date_key], backref="rentals")
    zone = relationship("DimCMHCZone", foreign_keys=[zone_key], backref="rentals")
