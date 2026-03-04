-- Mart: Unified Neighbourhood People Profile
-- Grain: one row per neighbourhood per census year (316 rows: 158 × 2)
-- Source: int_neighbourhood__people
-- Dashboard domains: Livability, Housing, People (Demographics + Amenities)
-- Replaces: mart_neighbourhood_demographics + mart_neighbourhood_amenities
-- BREAKING CHANGE (Sprint 16): grain changed from 158 to 316 rows; census_year column added.
-- Webapp queries must filter by census_year or aggregate across years.

{{ config(materialized='table') }}

select * from {{ ref('int_neighbourhood__people') }}
