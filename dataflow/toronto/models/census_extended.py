"""SQLAlchemy model for census extended wide-format scalar indicators."""

from sqlalchemy import Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .dimensions import RAW_TORONTO_SCHEMA


class FactCensusExtended(Base):
    """Wide-format scalar census indicators per neighbourhood.

    Path B: ~55 scalar indicators extracted directly from the Statistics Canada
    2021 Neighbourhood Profile XLSX. Intended as a primary source for
    int_neighbourhood__foundation (replacing the need for complex profile pivots
    for scalar indicators).

    Grain: One row per (neighbourhood_id, census_year).
    All indicator columns are nullable for Statistics Canada suppression.
    """

    __tablename__ = "fact_census_extended"
    __table_args__ = (
        UniqueConstraint(
            "neighbourhood_id",
            "census_year",
            name="uq_fact_census_extended_natural_key",
        ),
        Index(
            "ix_fact_census_extended_nbhd_year",
            "neighbourhood_id",
            "census_year",
        ),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    census_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Population
    population: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pop_0_to_14: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pop_15_to_24: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pop_25_to_64: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pop_65_plus: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Households
    total_private_dwellings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occupied_private_dwellings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_household_size: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    avg_household_income_after_tax: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Housing tenure and costs
    pct_owner_occupied: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_renter_occupied: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_suitable_housing: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    avg_shelter_cost_owner: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    avg_shelter_cost_renter: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    pct_shelter_cost_30pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Education
    pct_no_certificate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_high_school: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_college: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_university: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Labour force
    participation_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    employment_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    unemployment_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_employed_full_time: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Income
    median_after_tax_income: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    median_employment_income: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    lico_at_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    market_basket_measure_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Diversity / immigration
    pct_immigrants: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_recent_immigrants: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_visible_minority: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_indigenous: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Language
    pct_english_only: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_french_only: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_neither_official_lang: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_bilingual: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Mobility / migration
    pct_non_movers: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_movers_within_city: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_movers_from_other_city: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Commuting / transport
    pct_car_commuters: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_transit_commuters: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_active_commuters: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_work_from_home: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Additional indicators
    median_age: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_lone_parent_families: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    avg_number_of_children: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_dwellings_in_need_of_repair: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    pct_unaffordable_housing: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_overcrowded_housing: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    median_commute_minutes: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    pct_postsecondary: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_management_occupation: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_business_finance_admin: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_service_sector: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_trades_transport: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    population_density: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
