-- Mart: Neighbourhood Foundation
-- Dashboard Tab: Foundation
-- Grain: One row per neighbourhood per census year
--
-- Direct surface of int_neighbourhood__foundation.
-- Only includes columns with actual data (removes 49 NULL-only columns that were stubbed
-- in the schema but never populated from the source).
--
-- Use this mart when you need neighbourhood-level core demographics.
-- For extended metrics, see mart_neighbourhood_demographics (2021 only, fully populated).

with foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

final as (
    select
        -- Identifiers
        neighbourhood_id,
        land_area_sqkm,
        census_year,

        -- Core population
        population,
        population_density,

        -- Income (2021 observed; 2016-2020 CPI-imputed)
        median_household_income,
        average_household_income,
        income_quintile,
        is_imputed,

        -- Demographics
        median_age,
        unemployment_rate,
        education_bachelors_pct,
        average_dwelling_value,

        -- Tenure
        pct_owner_occupied,
        pct_renter_occupied

    from foundation
)

select * from final
