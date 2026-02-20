-- Mart: Toronto Rental Market Analysis
-- Final analytical table for rental market visualization
-- Grain: One row per zone per bedroom type per survey year

with rentals as (
    select * from {{ ref('int_rentals__annual') }}
),

-- Add year-over-year calculations
with_yoy as (
    select
        r.*,

        -- Previous year values
        lag(r.avg_rent, 1) over (
            partition by r.zone_code, r.bedroom_type
            order by r.year
        ) as avg_rent_prev_year,

        lag(r.vacancy_rate, 1) over (
            partition by r.zone_code, r.bedroom_type
            order by r.year
        ) as vacancy_rate_prev_year

    from rentals r
),

final as (
    select
        rental_id,
        date_key,
        full_date,
        year,
        quarter,
        zone_key,
        zone_code,
        zone_name,
        bedroom_type,
        rental_universe,
        avg_rent,
        vacancy_rate,
        turnover_rate,
        year_over_year_rent_change,
        reliability_code,
        vacant_units_estimate,

        -- Calculated year-over-year (if not provided)
        coalesce(
            year_over_year_rent_change,
            case
                when avg_rent_prev_year > 0
                then round(((avg_rent - avg_rent_prev_year) / avg_rent_prev_year) * 100, 2)
                else null
            end
        ) as rent_change_pct,

        vacancy_rate - vacancy_rate_prev_year as vacancy_rate_change

    from with_yoy
)

select * from final
