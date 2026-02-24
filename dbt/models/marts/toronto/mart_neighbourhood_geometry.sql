-- mart_neighbourhood_geometry: Canonical neighbourhood boundaries for map rendering
-- Grain: one row per neighbourhood (158 rows)

{{
    config(
        materialized='table'
    )
}}

select
    neighbourhood_id,
    neighbourhood_name,
    geometry
from {{ ref('stg_toronto__neighbourhoods') }}
