-- Mart: Neighbourhood Safety Analysis
-- Dashboard Tab: Safety
-- Grain: One row per neighbourhood per year
--
-- Raw incident counts only. Derived metrics (per-100k rates by type, crime index,
-- safety tier) are computed at query time by joining mart_neighbourhood_people for
-- population. safety_score and livability_score are the only computed columns stored here.

with crime as (
    select * from {{ ref('int_neighbourhood__crime_summary') }}
    where year >= 2016
),

-- Housing affordability index (neighbourhood × year)
housing as (
    select
        neighbourhood_id,
        year,
        housing_affordability_index
    from {{ ref('mart_neighbourhood_housing') }}
),

-- Amenity index — latest census year used as static value (infrastructure changes slowly)
people as (
    select
        neighbourhood_id,
        amenities_index
    from {{ ref('mart_neighbourhood_people') }}
    where census_year = (select max(census_year) from {{ ref('mart_neighbourhood_people') }})
),

-- Compute safety_score in a separate CTE — window functions cannot be nested in livability_score
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
        end as safety_score,

        -- Livability components (carried through for composite below)
        h.housing_affordability_index,
        p.amenities_index

    from crime c
    left join housing h
        on c.neighbourhood_id = h.neighbourhood_id
        and c.year = h.year
    left join people p
        on c.neighbourhood_id = p.neighbourhood_id
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
        safety_score,

        -- Livability score: composite (safety 30% + affordability 40% + amenity 30%)
        -- NULL when any component is missing — no coalesce fallback
        case
            when safety_score is not null
                and housing_affordability_index is not null
                and amenities_index is not null
            then round(
                (
                    safety_score * 0.30
                    + housing_affordability_index * 0.40
                    + (amenities_index / 2.5) * 0.30
                )::numeric,
                1
            )
            else null
        end as livability_score

    from scored
)

select * from final
