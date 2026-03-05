-- Mart: Neighbourhood Profile (wide format)
-- Grain: one row per neighbourhood per census_year (~158 rows, 2021 only)
-- Source: int_neighbourhood__profile_flat
-- 13 categories pivoted to profile_{abbrev}_{subcategory} / _pct named columns.
-- Replaces former long-format mart (neighbourhood × category × subcategory).

{{ config(materialized='table') }}

select * from {{ ref('int_neighbourhood__profile_flat') }}
