-- Staged census demographics by neighbourhood
-- Source: fact_census table
-- Grain: One row per neighbourhood per census year

with source as (
    select * from {{ source('toronto', 'fact_census') }}
),

staged as (
    select
        id as census_id,
        neighbourhood_id,
        census_year,
        population,
        population_density,
        median_household_income,
        average_household_income,
        unemployment_rate,
        pct_bachelors_or_higher,
        pct_owner_occupied,
        pct_renter_occupied,
        median_age,
        average_dwelling_value
    from source
)

select * from staged
