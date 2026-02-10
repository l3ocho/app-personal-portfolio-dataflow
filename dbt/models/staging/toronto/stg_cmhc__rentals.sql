-- Staged CMHC rental market survey data
-- Source: fact_rentals table loaded from CMHC/StatCan
-- Grain: One row per zone per bedroom type per survey year

with source as (
    select
        f.*,
        t.year as survey_year
    from {{ source('toronto', 'fact_rentals') }} f
    join {{ source('shared', 'dim_time') }} t on f.date_key = t.date_key
),

staged as (
    select
        id as rental_id,
        date_key,
        zone_key,
        survey_year as year,
        bedroom_type,
        universe as rental_universe,
        avg_rent,
        median_rent,
        vacancy_rate,
        availability_rate,
        turnover_rate,
        rent_change_pct as year_over_year_rent_change,
        reliability_code
    from source
)

select * from staged
