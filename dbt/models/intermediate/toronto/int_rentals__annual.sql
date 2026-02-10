-- Intermediate: Annual rental data enriched with dimensions
-- Joins rentals with time and zone dimensions for analysis

with rentals as (
    select * from {{ ref('stg_cmhc__rentals') }}
),

time_dim as (
    select * from {{ ref('stg_dimensions__time') }}
),

zone_dim as (
    select * from {{ ref('stg_dimensions__cmhc_zones') }}
),

enriched as (
    select
        r.rental_id,

        -- Time attributes
        t.date_key,
        t.full_date,
        t.year,
        t.month,
        t.quarter,

        -- Zone attributes
        z.zone_key,
        z.zone_code,
        z.zone_name,

        -- Bedroom type
        r.bedroom_type,

        -- Metrics
        r.rental_universe,
        r.avg_rent,
        r.median_rent,
        r.vacancy_rate,
        r.availability_rate,
        r.turnover_rate,
        r.year_over_year_rent_change,
        r.reliability_code,

        -- Calculated metrics
        case
            when r.rental_universe > 0 and r.vacancy_rate is not null
            then round(r.rental_universe * (r.vacancy_rate / 100), 0)
            else null
        end as vacant_units_estimate

    from rentals r
    inner join time_dim t on r.date_key = t.date_key
    inner join zone_dim z on r.zone_key = z.zone_key
)

select * from enriched
