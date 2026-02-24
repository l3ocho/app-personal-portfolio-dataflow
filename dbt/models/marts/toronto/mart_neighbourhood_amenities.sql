-- Mart: Neighbourhood Amenities Analysis
-- Dashboard Tab: Amenities
-- Grain: One row per neighbourhood per amenity year
--
-- Surfaces amenity scores, commute mode/duration/destination pivots,
-- and composite car dependency score from int_neighbourhood__amenity_scores.

with amenities as (
    select * from {{ ref('int_neighbourhood__amenity_scores') }}
),

-- City-wide averages for comparison
city_avg as (
    select
        year,
        avg(parks_per_1000)             as city_avg_parks,
        avg(schools_per_1000)           as city_avg_schools,
        avg(transit_per_1000)           as city_avg_transit,
        avg(total_amenities_per_1000)   as city_avg_total_amenities
    from amenities
    group by year
),

final as (
    select
        a.neighbourhood_id,
        a.population,
        a.land_area_sqkm,
        a.year,
        a.census_year,

        -- Raw amenity counts
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
        round(ca.city_avg_parks::numeric, 3)            as city_avg_parks_per_1000,
        round(ca.city_avg_schools::numeric, 3)          as city_avg_schools_per_1000,
        round(ca.city_avg_transit::numeric, 3)          as city_avg_transit_per_1000,

        -- Amenity index (100 = city average)
        case
            when ca.city_avg_total_amenities > 0
            then round(a.total_amenities_per_1000 / ca.city_avg_total_amenities * 100, 1)
            else null
        end as amenity_index,

        -- Category indices
        case when ca.city_avg_parks   > 0 then round(a.parks_per_1000   / ca.city_avg_parks   * 100, 1) else null end as parks_index,
        case when ca.city_avg_schools > 0 then round(a.schools_per_1000 / ca.city_avg_schools * 100, 1) else null end as schools_index,
        case when ca.city_avg_transit > 0 then round(a.transit_per_1000 / ca.city_avg_transit * 100, 1) else null end as transit_index,

        -- Amenity tier (1 = best, 5 = lowest)
        case
            when a.total_amenities_per_1000 is not null
            then ntile(5) over (
                partition by a.year,
                    (case when a.total_amenities_per_1000 is not null then 1 else 0 end)
                order by a.total_amenities_per_1000 desc
            )
            else null
        end as amenity_tier,

        -- Commute mode (raw counts)
        a.commute_car,
        a.commute_car_driver,
        a.commute_car_passenger,
        a.commute_transit,
        a.commute_walk,
        a.commute_bicycle,
        a.commute_other,

        -- Commute duration (raw counts)
        a.commute_under_15min,
        a.commute_15_29min,
        a.commute_30_44min,
        a.commute_45_59min,
        a.commute_60min_plus,

        -- Commute destination (raw counts)
        a.commute_usual_workplace,
        a.commute_work_from_home,
        a.commute_no_fixed_address,
        a.commute_outside_canada,

        -- Car dependency (from intermediate)
        a.car_dependency_pct,

        -- Derived: commute mode percentages
        -- total_commuters = sum of top-level mode buckets
        round(
            coalesce(a.commute_car, 0)::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        ) as commute_car_pct,

        round(
            coalesce(a.commute_transit, 0)::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        ) as commute_transit_pct,

        round(
            (coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0))::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        ) as commute_active_pct,

        -- Derived: long commute percentage (45 min+)
        round(
            (coalesce(a.commute_45_59min, 0) + coalesce(a.commute_60min_plus, 0))::numeric
            / nullif(
                coalesce(a.commute_under_15min, 0) + coalesce(a.commute_15_29min, 0)
                + coalesce(a.commute_30_44min, 0) + coalesce(a.commute_45_59min, 0)
                + coalesce(a.commute_60min_plus, 0),
                0
            ) * 100, 2
        ) as commute_long_pct

    from amenities a
    left join city_avg ca on a.year = ca.year
)

select * from final
