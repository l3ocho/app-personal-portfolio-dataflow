-- Intermediate: Year spine for analysis
-- Creates a row for each year from 2014-2025
-- Used to drive time-series analysis across all data sources

with years as (
    -- Generate years from available data sources
    -- Crime data: 2014-2024, Rentals: 2019-2025
    select generate_series(2014, 2025) as year
)

select year from years
