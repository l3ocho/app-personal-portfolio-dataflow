-- Staged CMHC zone dimension
-- Source: dim_cmhc_zone table
-- Grain: One row per zone

with source as (
    select * from {{ source('toronto', 'dim_cmhc_zone') }}
),

staged as (
    select
        zone_key,
        zone_code,
        zone_name
        -- geometry column excluded: CMHC does not provide zone boundaries
        -- Spatial analysis uses dim_neighbourhood geometry instead
    from source
)

select * from staged
