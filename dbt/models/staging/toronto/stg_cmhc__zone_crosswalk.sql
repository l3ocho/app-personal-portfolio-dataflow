-- Staged CMHC zone to neighbourhood crosswalk
-- Source: bridge_cmhc_neighbourhood table
-- Grain: One row per zone-neighbourhood intersection

with source as (
    select * from {{ source('toronto', 'bridge_cmhc_neighbourhood') }}
),

staged as (
    select
        id as crosswalk_id,
        cmhc_zone_code,
        neighbourhood_id,
        weight as area_weight
    from source
)

select * from staged
