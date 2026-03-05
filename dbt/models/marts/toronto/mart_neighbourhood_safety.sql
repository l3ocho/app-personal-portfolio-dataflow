-- Mart: Neighbourhood Safety Analysis
-- Dashboard Tab: Safety
-- Grain: One row per neighbourhood per year (2016–2025)
--
-- Raw incident counts only. Derived metrics (per-100k rates by type, crime index,
-- safety tier) are computed at query time by joining mart_neighbourhood_people for
-- population. safety_score is the only computed column stored here.

with crime as (
    select * from {{ ref('int_neighbourhood__crime_summary') }}
    where year >= 2016
),

-- Compute safety_score via window function
scored as (
    select
        c.neighbourhood_id,
        c.year,
        c.total_incidents,
        c.crime_rate_per_100k,
        c.yoy_change_pct as crime_yoy_change_pct,
        c.assault_count,
        c.auto_theft_count,
        c.break_enter_count,
        c.robbery_count,
        c.theft_over_count,
        c.homicide_count,

        -- Safety score: percentile inversion (higher = safer, 0-100)
        case
            when c.crime_rate_per_100k is not null
            then round(
                ((1 - percent_rank() over (
                    partition by c.year
                    order by c.crime_rate_per_100k
                )) * 100)::numeric,
                1
            )
            else null
        end as safety_score

    from crime c
),

final as (
    select
        neighbourhood_id,
        year,
        total_incidents,
        crime_rate_per_100k,
        crime_yoy_change_pct,
        assault_count,
        auto_theft_count,
        break_enter_count,
        robbery_count,
        theft_over_count,
        homicide_count,
        safety_score

    from scored
)

select * from final
