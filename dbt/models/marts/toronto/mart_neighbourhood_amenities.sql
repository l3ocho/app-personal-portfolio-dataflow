-- Mart: Neighbourhood Amenities Analysis
-- Dashboard Tab: Amenities
-- Grain: One row per neighbourhood per year

with amenities as (
    select * from {{ ref('int_neighbourhood__amenity_scores') }}
),

-- City-wide averages for comparison
city_avg as (
    select
        year,
        avg(parks_per_1000) as city_avg_parks,
        avg(schools_per_1000) as city_avg_schools,
        avg(transit_per_1000) as city_avg_transit,
        avg(total_amenities_per_1000) as city_avg_total_amenities
    from amenities
    group by year
),

final as (
    select
        a.neighbourhood_id,
        a.neighbourhood_name,
        a.geometry,
        a.population,
        a.land_area_sqkm,
        a.year,

        -- Raw counts
        a.parks_count,
        a.schools_count,
        a.transit_count,
        a.libraries_count,
        a.community_centres_count,
        a.childcare_count,
        a.total_amenities,

        -- Per 1000 population
        a.parks_per_1000,
        a.schools_per_1000,
        a.transit_per_1000,
        a.total_amenities_per_1000,

        -- Per square km
        a.amenities_per_sqkm,

        -- City averages
        round(ca.city_avg_parks::numeric, 3) as city_avg_parks_per_1000,
        round(ca.city_avg_schools::numeric, 3) as city_avg_schools_per_1000,
        round(ca.city_avg_transit::numeric, 3) as city_avg_transit_per_1000,

        -- Amenity index (100 = city average)
        case
            when ca.city_avg_total_amenities > 0
            then round(a.total_amenities_per_1000 / ca.city_avg_total_amenities * 100, 1)
            else null
        end as amenity_index,

        -- Category indices
        case
            when ca.city_avg_parks > 0
            then round(a.parks_per_1000 / ca.city_avg_parks * 100, 1)
            else null
        end as parks_index,

        case
            when ca.city_avg_schools > 0
            then round(a.schools_per_1000 / ca.city_avg_schools * 100, 1)
            else null
        end as schools_index,

        case
            when ca.city_avg_transit > 0
            then round(a.transit_per_1000 / ca.city_avg_transit * 100, 1)
            else null
        end as transit_index,

        -- Amenity tier (1 = best, 5 = lowest; NULL when no population data)
        case
            when a.total_amenities_per_1000 is not null
            then ntile(5) over (
                partition by a.year,
                    (case when a.total_amenities_per_1000 is not null then 1 else 0 end)
                order by a.total_amenities_per_1000 desc
            )
            else null
        end as amenity_tier

    from amenities a
    left join city_avg ca on a.year = ca.year
)

select * from final
