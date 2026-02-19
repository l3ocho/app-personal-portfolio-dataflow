-- Staged neighbourhood community profile data
-- Source: fact_neighbourhood_profile table
-- Grain: One row per (neighbourhood_id, census_year, category, subcategory, level)
-- Normalizes casing and keeps suppressed (null count) rows for completeness

with source as (
    select * from {{ source('toronto', 'fact_neighbourhood_profile') }}
),

staged as (
    select
        id                                      as profile_id,
        neighbourhood_id,
        census_year,
        lower(trim(category))                   as category,
        lower(trim(subcategory))                as subcategory,
        count,
        level
    from source
)

select * from staged
