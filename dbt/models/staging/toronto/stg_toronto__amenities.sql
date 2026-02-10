-- Staged amenity counts by neighbourhood
-- Source: fact_amenities table
-- Grain: One row per neighbourhood per amenity type per year

with source as (
    select * from {{ source('toronto', 'fact_amenities') }}
),

staged as (
    select
        id as amenity_id,
        neighbourhood_id,
        amenity_type,
        count as amenity_count,
        year as amenity_year
    from source
)

select * from staged
