-- Mart: Neighbourhood Livability Scores
-- Dashboard Tab: Livability
-- Grain: one row per neighbourhood per year (housing year spine)
-- Sources: mart_neighbourhood_safety, mart_neighbourhood_housing, mart_neighbourhood_people
--
-- Composite livability score = safety (30%) + affordability (40%) + amenities (30%)
-- livability_score is NULL when any component is missing — no coalesce fallback.
-- Raw metrics (crime rates, rents, population) live in their domain marts.
-- Join mart_neighbourhood_safety, mart_neighbourhood_housing, mart_neighbourhood_people
-- at query time to retrieve raw metrics for display.
--
-- Component scores:
--   affordability_score = housing_affordability_index (100 = city avg; lower = more affordable)
--   amenity_score       = amenities_index / 2.5 (normalises 0–200 index to 0–80 operational range)

{{ config(materialized='table') }}

with housing as (
    select
        neighbourhood_id,
        year,
        housing_affordability_index as affordability_score
    from {{ ref('mart_neighbourhood_housing') }}
),

safety as (
    select
        neighbourhood_id,
        year,
        safety_score
    from {{ ref('mart_neighbourhood_safety') }}
),

-- Amenities: latest census year used as static value (infrastructure changes slowly)
people as (
    select
        neighbourhood_id,
        amenities_index
    from {{ ref('mart_neighbourhood_people') }}
    where census_year = (select max(census_year) from {{ ref('mart_neighbourhood_people') }})
)

select
    h.neighbourhood_id,
    h.year,

    -- Affordability component: housing_affordability_index (100 = city average)
    h.affordability_score,

    -- Amenity component: normalise amenities_index (0–200 scale) to 0–100 operational range
    case
        when p.amenities_index is not null
        then round((p.amenities_index / 2.5)::numeric, 1)
        else null
    end as amenity_score,

    -- Composite livability score (0–100): NULL when any component is missing
    case
        when s.safety_score is not null
            and h.affordability_score is not null
            and p.amenities_index is not null
        then round(
            (
                s.safety_score * 0.30
                + h.affordability_score * 0.40
                + (p.amenities_index / 2.5) * 0.30
            )::numeric, 1
        )
        else null
    end as livability_score

from housing h
left join safety s
    on h.neighbourhood_id = s.neighbourhood_id
    and h.year = s.year
left join people p
    on h.neighbourhood_id = p.neighbourhood_id
