-- Intermediate: Normalized amenities per 1000 population
-- Pivots amenity types and calculates per-capita metrics
-- Grain: One row per neighbourhood per year

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
),

amenities as (
    select * from {{ ref('stg_toronto__amenities') }}
),

-- Aggregate amenity types
amenities_by_year as (
    select
        neighbourhood_id,
        amenity_year as year,
        sum(case when amenity_type = 'park' then amenity_count else 0 end) as parks_count,
        sum(case when amenity_type = 'school' then amenity_count else 0 end) as schools_count,
        sum(case when amenity_type = 'transit_stop' then amenity_count else 0 end) as transit_count,
        sum(case when amenity_type = 'library' then amenity_count else 0 end) as libraries_count,
        sum(case when amenity_type = 'community_centre' then amenity_count else 0 end) as community_centres_count,
        sum(case when amenity_type = 'childcare' then amenity_count else 0 end) as childcare_count,
        sum(amenity_count) as total_amenities
    from amenities
    group by neighbourhood_id, amenity_year
),

amenity_scores as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        c.population,
        case
            when c.population_density > 0
            then round(c.population::numeric / c.population_density, 2)
            else null
        end as land_area_sqkm,

        coalesce(a.year, 2021) as year,

        -- Raw counts
        a.parks_count,
        a.schools_count,
        a.transit_count,
        a.libraries_count,
        a.community_centres_count,
        a.childcare_count,
        a.total_amenities,

        -- Per 1000 population
        case when c.population > 0
            then round(a.parks_count::numeric / c.population * 1000, 3)
            else null
        end as parks_per_1000,

        case when c.population > 0
            then round(a.schools_count::numeric / c.population * 1000, 3)
            else null
        end as schools_per_1000,

        case when c.population > 0
            then round(a.transit_count::numeric / c.population * 1000, 3)
            else null
        end as transit_per_1000,

        case when c.population > 0
            then round(a.total_amenities::numeric / c.population * 1000, 3)
            else null
        end as total_amenities_per_1000,

        -- Per square km
        case when c.population_density > 0
            then round(
                a.total_amenities::numeric
                / (c.population::numeric / c.population_density),
                2
            )
            else null
        end as amenities_per_sqkm

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    left join amenities_by_year a on n.neighbourhood_id = a.neighbourhood_id
)

select * from amenity_scores
