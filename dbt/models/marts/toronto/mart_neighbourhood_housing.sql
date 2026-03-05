-- Mart: Neighbourhood Housing Analysis (unified)
-- Dashboard Tab: Housing
-- Grain: one row per neighbourhood per rental year
-- Source: int_neighbourhood__housing_unified
--
-- Replaces former mart_neighbourhood_housing (census-only scalar metrics) and
-- mart_neighbourhood_housing_rentals (bedroom × year long format).
-- Bedroom-type metrics are pivoted to wide format (4 columns per metric).
-- Columns duplicated in mart_neighbourhood_people are excluded:
--   median_household_income, average_dwelling_value, income_quintile,
--   shelter costs, dwelling/bedroom/construction pivots, fit scores.

{{ config(materialized='table') }}

with base as (
    select * from {{ ref('int_neighbourhood__housing_unified') }}
),

-- Safety score (neighbourhood × year) — for livability composite
safety as (
    select
        neighbourhood_id,
        year,
        safety_score
    from {{ ref('mart_neighbourhood_safety') }}
),

-- Amenity index — latest census year used as static value (infrastructure changes slowly)
people as (
    select
        neighbourhood_id,
        amenities_index
    from {{ ref('mart_neighbourhood_people') }}
    where census_year = (select max(census_year) from {{ ref('mart_neighbourhood_people') }})
)

select
    base.*,

    -- Livability score: composite (safety 30% + affordability 40% + amenity 30%)
    -- NULL when any component is missing — no coalesce fallback
    case
        when s.safety_score is not null
            and base.housing_affordability_index is not null
            and p.amenities_index is not null
        then round(
            (
                s.safety_score * 0.30
                + base.housing_affordability_index * 0.40
                + (p.amenities_index / 2.5) * 0.30
            )::numeric, 1
        )
        else null
    end as livability_score

from base
left join safety s
    on base.neighbourhood_id = s.neighbourhood_id
    and base.year = s.year
left join people p
    on base.neighbourhood_id = p.neighbourhood_id
