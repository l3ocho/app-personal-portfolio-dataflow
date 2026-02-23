"""Pydantic schema for census extended scalar indicators.

Path B extraction: ~55 wide-format scalar indicators per neighbourhood
extracted directly from the Statistics Canada 2021 Neighbourhood Profile XLSX.

Natural key: (neighbourhood_id, census_year).
"""

from pydantic import BaseModel, Field


class CensusExtendedRecord(BaseModel):
    """Wide-format scalar census indicators for a neighbourhood.

    Contains ~55 scalar indicators extracted from the Statistics Canada
    2021 Census Profile XLSX. These are pre-computed aggregates and
    percentages that would otherwise require complex profile pivots.

    All indicator fields are nullable to handle Statistics Canada
    suppression codes (x, X, F, ..) for small population cells.
    """

    # Natural key
    neighbourhood_id: int = Field(ge=1, le=200, description="Neighbourhood ID (AREA_ID)")
    census_year: int = Field(ge=2016, le=2030, description="Census year")

    # Population
    population: int | None = Field(default=None, ge=0, description="Total population")
    pop_0_to_14: int | None = Field(default=None, ge=0, description="Population aged 0-14")
    pop_15_to_24: int | None = Field(default=None, ge=0, description="Population aged 15-24")
    pop_25_to_64: int | None = Field(default=None, ge=0, description="Population aged 25-64")
    pop_65_plus: int | None = Field(default=None, ge=0, description="Population aged 65+")

    # Households
    total_private_dwellings: int | None = Field(
        default=None, ge=0, description="Total private dwellings"
    )
    occupied_private_dwellings: int | None = Field(
        default=None, ge=0, description="Occupied private dwellings"
    )
    avg_household_size: float | None = Field(
        default=None, ge=0, description="Average household size (persons)"
    )
    avg_household_income_after_tax: float | None = Field(
        default=None, ge=0, description="Average household income after tax (CAD)"
    )

    # Housing tenure and costs
    pct_owner_occupied: float | None = Field(
        default=None, ge=0, le=100, description="% owner-occupied dwellings"
    )
    pct_renter_occupied: float | None = Field(
        default=None, ge=0, le=100, description="% renter-occupied dwellings"
    )
    pct_suitable_housing: float | None = Field(
        default=None, ge=0, le=100, description="% in suitable housing (not overcrowded)"
    )
    avg_shelter_cost_owner: float | None = Field(
        default=None, ge=0, description="Average monthly shelter cost for owners (CAD)"
    )
    avg_shelter_cost_renter: float | None = Field(
        default=None, ge=0, description="Average monthly shelter cost for renters (CAD)"
    )
    pct_shelter_cost_30pct: float | None = Field(
        default=None, ge=0, le=100,
        description="% spending 30%+ of income on shelter"
    )

    # Education
    pct_no_certificate: float | None = Field(
        default=None, ge=0, le=100, description="% with no certificate, diploma or degree"
    )
    pct_high_school: float | None = Field(
        default=None, ge=0, le=100, description="% with high school diploma"
    )
    pct_college: float | None = Field(
        default=None, ge=0, le=100, description="% with college/trades certificate"
    )
    pct_university: float | None = Field(
        default=None, ge=0, le=100, description="% with university degree or higher"
    )

    # Labour force
    participation_rate: float | None = Field(
        default=None, ge=0, le=100, description="Labour force participation rate (%)"
    )
    employment_rate: float | None = Field(
        default=None, ge=0, le=100, description="Employment rate (%)"
    )
    unemployment_rate: float | None = Field(
        default=None, ge=0, le=100, description="Unemployment rate (%)"
    )
    pct_employed_full_time: float | None = Field(
        default=None, ge=0, le=100, description="% employed full time"
    )

    # Income
    median_after_tax_income: float | None = Field(
        default=None, ge=0, description="Median after-tax income of households (CAD)"
    )
    median_employment_income: float | None = Field(
        default=None, ge=0, description="Median employment income (CAD)"
    )
    lico_at_rate: float | None = Field(
        default=None, ge=0, le=100,
        description="% in low income (LICO after-tax)"
    )
    market_basket_measure_rate: float | None = Field(
        default=None, ge=0, le=100,
        description="% in low income (Market Basket Measure)"
    )

    # Diversity / immigration
    pct_immigrants: float | None = Field(
        default=None, ge=0, le=100, description="% immigrants"
    )
    pct_recent_immigrants: float | None = Field(
        default=None, ge=0, le=100, description="% recent immigrants (arrived 2016-2021)"
    )
    pct_visible_minority: float | None = Field(
        default=None, ge=0, le=100, description="% visible minority"
    )
    pct_indigenous: float | None = Field(
        default=None, ge=0, le=100, description="% Indigenous identity"
    )

    # Language
    pct_english_only: float | None = Field(
        default=None, ge=0, le=100, description="% with knowledge of English only"
    )
    pct_french_only: float | None = Field(
        default=None, ge=0, le=100, description="% with knowledge of French only"
    )
    pct_neither_official_lang: float | None = Field(
        default=None, ge=0, le=100, description="% with no knowledge of official languages"
    )
    pct_bilingual: float | None = Field(
        default=None, ge=0, le=100, description="% bilingual (English and French)"
    )

    # Mobility / migration
    pct_non_movers: float | None = Field(
        default=None, ge=0, le=100, description="% non-movers (same address 5 years ago)"
    )
    pct_movers_within_city: float | None = Field(
        default=None, ge=0, le=100, description="% internal migrants within city"
    )
    pct_movers_from_other_city: float | None = Field(
        default=None, ge=0, le=100, description="% migrants from other city/province"
    )

    # Commuting / transport
    pct_car_commuters: float | None = Field(
        default=None, ge=0, le=100, description="% commuting by car, truck or van"
    )
    pct_transit_commuters: float | None = Field(
        default=None, ge=0, le=100, description="% commuting by public transit"
    )
    pct_active_commuters: float | None = Field(
        default=None, ge=0, le=100, description="% commuting by walking or cycling"
    )
    pct_work_from_home: float | None = Field(
        default=None, ge=0, le=100, description="% working from home"
    )

    # Additional indicators (to reach ~55 total)
    median_age: float | None = Field(
        default=None, ge=0, le=120, description="Median age"
    )
    pct_lone_parent_families: float | None = Field(
        default=None, ge=0, le=100, description="% lone-parent families"
    )
    avg_number_of_children: float | None = Field(
        default=None, ge=0, description="Average number of children per family"
    )
    pct_dwellings_in_need_of_repair: float | None = Field(
        default=None, ge=0, le=100, description="% dwellings in need of major repairs"
    )
    pct_unaffordable_housing: float | None = Field(
        default=None, ge=0, le=100, description="% in unaffordable housing (30%+ on shelter)"
    )
    pct_overcrowded_housing: float | None = Field(
        default=None, ge=0, le=100, description="% in overcrowded housing"
    )
    median_commute_minutes: float | None = Field(
        default=None, ge=0, description="Median commute duration (minutes)"
    )
    pct_postsecondary: float | None = Field(
        default=None, ge=0, le=100, description="% with postsecondary certificate or higher"
    )
    pct_management_occupation: float | None = Field(
        default=None, ge=0, le=100, description="% in management occupations"
    )
    pct_business_finance_admin: float | None = Field(
        default=None, ge=0, le=100, description="% in business/finance/admin occupations"
    )
    pct_service_sector: float | None = Field(
        default=None, ge=0, le=100, description="% in service sector occupations"
    )
    pct_trades_transport: float | None = Field(
        default=None, ge=0, le=100, description="% in trades/transport occupations"
    )
    population_density: float | None = Field(
        default=None, ge=0, description="Population density per square kilometre"
    )

    model_config = {"str_strip_whitespace": True}
