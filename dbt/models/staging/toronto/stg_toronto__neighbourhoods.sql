-- Staged Toronto neighbourhood dimension
-- Source: dim_neighbourhood table
-- Grain: One row per neighbourhood (158 total)

with source as (
    select * from {{ source('toronto', 'dim_neighbourhood') }}
),

staged as (
    select
        neighbourhood_id,
        name as neighbourhood_name,
        geometry,
        population,
        coalesce(
            land_area_sqkm,
            round((ST_Area(geometry::geography) / 1000000.0)::numeric, 4)
        ) as land_area_sqkm,
        pop_density_per_sqkm,
        pct_bachelors_or_higher,
        median_household_income,
        pct_owner_occupied,
        pct_renter_occupied,
        census_year
    from source
)

select * from staged
