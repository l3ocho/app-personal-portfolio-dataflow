-- Intermediate: Normalized amenities per 1000 population + commute profile pivots
-- Grain: One row per neighbourhood per amenity year
--
-- Uses int_neighbourhood__foundation for population base (replaces stg_toronto__census).
-- Adds commute mode, duration, and destination pivots from stg_toronto__profiles.

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

amenities as (
    select * from {{ ref('stg_toronto__amenities') }}
),

-- Aggregate amenity types by neighbourhood and year
amenities_by_year as (
    select
        neighbourhood_id,
        amenity_year as year,
        sum(case when amenity_type = 'park'              then amenity_count else 0 end) as parks_count,
        sum(case when amenity_type = 'school'            then amenity_count else 0 end) as schools_count,
        sum(case when amenity_type = 'transit_stop'      then amenity_count else 0 end) as transit_count,
        sum(case when amenity_type = 'library'           then amenity_count else 0 end) as libraries_count,
        sum(case when amenity_type = 'community_centre'  then amenity_count else 0 end) as community_centres_count,
        sum(case when amenity_type = 'childcare'         then amenity_count else 0 end) as childcare_count,
        sum(amenity_count) as total_amenities
    from amenities
    group by neighbourhood_id, amenity_year
),

-- Commute mode, duration, and destination pivots
-- Grain: one row per (neighbourhood_id, census_year)
profile_commute as (
    select
        neighbourhood_id,
        census_year,

        -- Commute mode (indent_level=2 = top-level mode buckets)
        max(case when category = 'commute_mode' and subcategory = 'car, truck or van'   then count end) as commute_car,
        max(case when category = 'commute_mode' and subcategory = 'public transit'       then count end) as commute_transit,
        max(case when category = 'commute_mode' and subcategory = 'walked'               then count end) as commute_walk,
        max(case when category = 'commute_mode' and subcategory = 'bicycle'              then count end) as commute_bicycle,
        max(case when category = 'commute_mode' and subcategory = 'other method'         then count end) as commute_other,

        -- Commute mode detail (indent_level=4 = driver/passenger split)
        max(case when category = 'commute_mode' and subcategory = 'car, truck or van - as a driver'    then count end) as commute_car_driver,
        max(case when category = 'commute_mode' and subcategory = 'car, truck or van - as a passenger' then count end) as commute_car_passenger,

        -- Commute duration
        max(case when category = 'commute_duration' and subcategory = 'less than 15 minutes' then count end) as commute_under_15min,
        max(case when category = 'commute_duration' and subcategory = '15 to 29 minutes'     then count end) as commute_15_29min,
        max(case when category = 'commute_duration' and subcategory = '30 to 44 minutes'     then count end) as commute_30_44min,
        max(case when category = 'commute_duration' and subcategory = '45 to 59 minutes'     then count end) as commute_45_59min,
        max(case when category = 'commute_duration' and subcategory = '60 minutes and over'  then count end) as commute_60min_plus,

        -- Commute destination
        max(case when category = 'commute_destination' and subcategory = 'usual place of work'       then count end) as commute_usual_workplace,
        max(case when category = 'commute_destination' and subcategory = 'worked at home'            then count end) as commute_work_from_home,
        max(case when category = 'commute_destination' and subcategory = 'no fixed workplace address' then count end) as commute_no_fixed_address,
        max(case when category = 'commute_destination' and subcategory = 'worked outside canada'      then count end) as commute_outside_canada

    from {{ ref('stg_toronto__profiles') }}
    where category in ('commute_mode', 'commute_duration', 'commute_destination')
    group by neighbourhood_id, census_year
),

amenity_scores as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        n.land_area_sqkm,

        f.population,
        f.census_year,

        coalesce(a.year, 2021) as year,

        -- Raw amenity counts
        a.parks_count,
        a.schools_count,
        a.transit_count,
        a.libraries_count,
        a.community_centres_count,
        a.childcare_count,
        a.total_amenities,

        -- Per 1000 population
        case when f.population > 0
            then round(a.parks_count::numeric / f.population * 1000, 3)
            else null
        end as parks_per_1000,

        case when f.population > 0
            then round(a.schools_count::numeric / f.population * 1000, 3)
            else null
        end as schools_per_1000,

        case when f.population > 0
            then round(a.transit_count::numeric / f.population * 1000, 3)
            else null
        end as transit_per_1000,

        case when f.population > 0
            then round(a.total_amenities::numeric / f.population * 1000, 3)
            else null
        end as total_amenities_per_1000,

        -- Per square km
        case when n.land_area_sqkm > 0
            then round(a.total_amenities::numeric / n.land_area_sqkm, 2)
            else null
        end as amenities_per_sqkm,

        -- Commute mode pivots
        pc.commute_car,
        pc.commute_car_driver,
        pc.commute_car_passenger,
        pc.commute_transit,
        pc.commute_walk,
        pc.commute_bicycle,
        pc.commute_other,

        -- Commute duration pivots
        pc.commute_under_15min,
        pc.commute_15_29min,
        pc.commute_30_44min,
        pc.commute_45_59min,
        pc.commute_60min_plus,

        -- Commute destination pivots
        pc.commute_usual_workplace,
        pc.commute_work_from_home,
        pc.commute_no_fixed_address,
        pc.commute_outside_canada,

        -- Car dependency composite: car commuters / all commuters (%)
        round(
            coalesce(pc.commute_car, 0)::numeric
            / nullif(
                coalesce(pc.commute_car, 0) + coalesce(pc.commute_transit, 0)
                + coalesce(pc.commute_walk, 0) + coalesce(pc.commute_bicycle, 0)
                + coalesce(pc.commute_other, 0),
                0
            ) * 100,
            2
        ) as car_dependency_pct

    from neighbourhoods n
    left join amenities_by_year a on n.neighbourhood_id = a.neighbourhood_id
    -- Use most recent foundation census data available for each amenity year
    left join foundation f
        on n.neighbourhood_id = f.neighbourhood_id
        and f.census_year = (
            select max(f2.census_year)
            from {{ ref('int_neighbourhood__foundation') }} f2
            where f2.neighbourhood_id = n.neighbourhood_id
            and f2.census_year <= coalesce(a.year, 2024)
        )
    -- Join commute pivots at the resolved census year
    left join profile_commute pc
        on n.neighbourhood_id = pc.neighbourhood_id
        and pc.census_year = f.census_year
)

select * from amenity_scores
