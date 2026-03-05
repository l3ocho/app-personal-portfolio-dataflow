-- Mart: Neighbourhood Housing Analysis (unified)
-- Dashboard Tab: Housing
-- Grain: one row per neighbourhood per rental year
-- Source: int_neighbourhood__housing_unified
--
-- Replaces former mart_neighbourhood_housing (census-only scalar metrics) and
-- mart_neighbourhood_housing_rentals (bedroom × year long format).
-- Bedroom-type metrics are pivoted to wide format (4 columns per metric).
-- Columns duplicated in mart_neighbourhood_people are excluded:
--   median_household_income, average_dwelling_value, income_quintile,
--   shelter costs, dwelling/bedroom/construction pivots, fit scores.

{{ config(materialized='table') }}

select * from {{ ref('int_neighbourhood__housing_unified') }}
