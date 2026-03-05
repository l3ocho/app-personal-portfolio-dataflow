-- Mart: Wide-format neighbourhood profile
-- Grain: one row per neighbourhood per census_year (~158 rows, 2021 only currently)
-- Source: int_neighbourhood__profile_wide
-- Additive — does NOT replace mart_neighbourhood_profile (long format kept for
-- dynamic webapp queries e.g. get_profile_category, get_place_of_birth_tree)

{{ config(materialized='table') }}

select * from {{ ref('int_neighbourhood__profile_wide') }}
