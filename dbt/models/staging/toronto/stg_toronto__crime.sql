-- Staged crime statistics by neighbourhood
-- Source: fact_crime table
-- Grain: One row per neighbourhood per year per crime type

with source as (
    select * from {{ source('toronto', 'fact_crime') }}
),

staged as (
    select
        id as crime_id,
        neighbourhood_id,
        year as crime_year,
        crime_type,
        count as incident_count,
        rate_per_100k
    from source
)

select * from staged
