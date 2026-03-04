-- Mart: Unified Neighbourhood People Profile
-- Grain: one row per neighbourhood (latest year only, 158 rows)
-- Source: int_neighbourhood__people
-- Dashboard domains: Livability, Housing, People (Demographics + Amenities)
-- Replaces: mart_neighbourhood_demographics + mart_neighbourhood_amenities

{{ config(materialized='table') }}

select * from {{ ref('int_neighbourhood__people') }}
