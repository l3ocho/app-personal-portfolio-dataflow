-- Intermediate: Unified people profile per neighbourhood × census year
-- Grain: one row per neighbourhood per census year (316 rows: 158 × 2)
-- Sources: int_neighbourhood__foundation (all census years)
--          int_neighbourhood__amenity_scores (latest amenity year, joined to both census years)
--          stg_toronto__neighbourhoods (geometry + name + land_area)
-- NOTE: Does NOT reference any mart. Built directly from intermediates.
-- City averages and indices are partitioned by census_year so 2016 and 2021
-- are each calibrated within their own year.

with neighbourhoods as (
    select
        neighbourhood_id,
        neighbourhood_name,
        geometry,
        land_area_sqkm
    from {{ ref('stg_toronto__neighbourhoods') }}
),

-- All census years from foundation (316 rows: 158 × 2 census years)
foundation_all as (
    select *
    from {{ ref('int_neighbourhood__foundation') }}
),

-- Latest amenity year per neighbourhood
amenity_latest as (
    select *
    from {{ ref('int_neighbourhood__amenity_scores') }}
    where year = (
        select max(year)
        from {{ ref('int_neighbourhood__amenity_scores') }}
    )
),

-- City-wide averages partitioned by census_year
-- Amenity averages use latest amenity data joined to the census year's population
city_avg as (
    select
        f.census_year,
        avg(f.population::numeric / nullif(f.land_area_sqkm, 0))              as city_avg_pop_density,
        avg(f.median_age)                                                      as city_avg_age,
        avg(f.median_household_income)                                         as city_avg_income_md,
        avg(f.average_household_income)                                        as city_avg_income_avg,
        avg(f.unemployment_rate)                                               as city_avg_unemployment,
        avg(a.parks_per_1000)                                                  as city_avg_parks_1k,
        avg(a.schools_per_1000)                                                as city_avg_schools_1k,
        avg(a.transit_per_1000)                                                as city_avg_transit_1k,
        avg(a.libraries_count::numeric / nullif(f.population, 0) * 1000)      as city_avg_libraries_1k,
        avg(a.childcare_count::numeric / nullif(f.population, 0) * 1000)      as city_avg_childcare_1k,
        avg(a.community_centres_count::numeric / nullif(f.population, 0) * 1000) as city_avg_commcentres_1k,
        avg(a.total_amenities_per_1000)                                        as city_avg_amenities_1k
    from foundation_all f
    join amenity_latest a using (neighbourhood_id)
    group by f.census_year
),

-- Amenity tier: ntile(5) over all neighbourhoods using latest amenity data (1=best, 5=lowest)
amenity_tiers as (
    select
        neighbourhood_id,
        case
            when total_amenities_per_1000 is not null
            then ntile(5) over (order by total_amenities_per_1000 desc)
            else null
        end as amenities_tier
    from amenity_latest
),

final as (
    select
        -- ── Identity ──────────────────────────────────────────────────────
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        n.land_area_sqkm,
        f.census_year,

        -- ── Population ────────────────────────────────────────────────────
        f.population                                                            as pop,
        round(f.population::numeric / nullif(n.land_area_sqkm, 0), 2)         as pop_density,

        -- Age cohorts (from census_extended via foundation, 2021 only; NULL for 2016)
        f.pop_0_to_14,
        f.pop_15_to_24,
        f.pop_25_to_64,
        f.pop_65_plus,

        -- ── Age ───────────────────────────────────────────────────────────
        f.median_age                                                            as age_md,
        round(ca.city_avg_age::numeric, 2)                                     as age_city_avg,
        case
            when ca.city_avg_age > 0
            then round(f.median_age / ca.city_avg_age * 100, 1)
            else null
        end                                                                     as age_index,

        -- ── Education ─────────────────────────────────────────────────────
        f.education_bachelors_pct                                              as edu_bachelors_pct,
        case
            when f.education_bachelors_pct is not null
            then round(100 - f.education_bachelors_pct, 2)
            else null
        end                                                                     as edu_nonbachelors_pct,

        -- ── Income ────────────────────────────────────────────────────────
        f.median_household_income                                              as income_household_md,
        f.average_household_income                                             as income_household_avg,
        f.income_quintile,
        f.is_imputed,
        round(ca.city_avg_income_md::numeric, 2)                              as income_city_avg,
        case
            when ca.city_avg_income_md > 0
            then round(f.median_household_income / ca.city_avg_income_md * 100, 1)
            else null
        end                                                                     as income_index,

        -- ── Unemployment ──────────────────────────────────────────────────
        f.unemployment_rate,
        round(ca.city_avg_unemployment::numeric, 4)                           as unemployment_city_rate,
        case
            when ca.city_avg_unemployment > 0
            then round(f.unemployment_rate / ca.city_avg_unemployment * 100, 1)
            else null
        end                                                                     as unemployment_index,

        -- ── Housing ───────────────────────────────────────────────────────
        f.pct_owner_occupied                                                   as housing_occupied_owner,
        f.pct_renter_occupied                                                  as housing_occupied_renter,
        f.average_dwelling_value                                               as housing_dwelling_value_avg,
        -- Herfindahl complement: 0 = all one tenure, ~50 = perfectly mixed
        round(
            (1 - (
                power(coalesce(f.pct_owner_occupied, 0) / 100, 2) +
                power(coalesce(f.pct_renter_occupied, 0) / 100, 2)
            )) * 100,
            3
        )                                                                       as housing_tenure_diversity_index,

        -- ── Amenities: Parks ──────────────────────────────────────────────
        a.parks_count                                                          as amenities_parks,
        a.parks_per_1000                                                       as amenities_parks_1k,
        round(ca.city_avg_parks_1k::numeric, 3)                               as amenities_parks_city_1k,
        case
            when ca.city_avg_parks_1k > 0
            then round(a.parks_per_1000 / ca.city_avg_parks_1k * 100, 1)
            else null
        end                                                                     as amenities_parks_index,

        -- ── Amenities: Schools ────────────────────────────────────────────
        a.schools_count                                                        as amenities_schools,
        a.schools_per_1000                                                     as amenities_schools_1k,
        round(ca.city_avg_schools_1k::numeric, 3)                             as amenities_schools_city_1k,
        case
            when ca.city_avg_schools_1k > 0
            then round(a.schools_per_1000 / ca.city_avg_schools_1k * 100, 1)
            else null
        end                                                                     as amenities_schools_index,

        -- ── Amenities: Libraries ─────────────────────────────────────────
        a.libraries_count                                                      as amenities_libraries,
        round(a.libraries_count::numeric / nullif(f.population, 0) * 1000, 3) as amenities_libraries_1k,
        round(ca.city_avg_libraries_1k::numeric, 3)                           as amenities_libraries_city_1k,
        case
            when ca.city_avg_libraries_1k > 0
            then round(
                (a.libraries_count::numeric / nullif(f.population, 0) * 1000)
                / ca.city_avg_libraries_1k * 100, 1)
            else null
        end                                                                     as amenities_libraries_index,

        -- ── Amenities: Childcare ─────────────────────────────────────────
        a.childcare_count                                                      as amenities_childcare,
        round(a.childcare_count::numeric / nullif(f.population, 0) * 1000, 3) as amenities_childcare_1k,
        round(ca.city_avg_childcare_1k::numeric, 3)                           as amenities_childcare_city_1k,
        case
            when ca.city_avg_childcare_1k > 0
            then round(
                (a.childcare_count::numeric / nullif(f.population, 0) * 1000)
                / ca.city_avg_childcare_1k * 100, 1)
            else null
        end                                                                     as amenities_childcare_index,

        -- ── Amenities: Community Centres ─────────────────────────────────
        a.community_centres_count                                              as amenities_commcentres,
        round(a.community_centres_count::numeric / nullif(f.population, 0) * 1000, 3) as amenities_commcentres_1k,
        round(ca.city_avg_commcentres_1k::numeric, 3)                         as amenities_commcentres_city_1k,
        case
            when ca.city_avg_commcentres_1k > 0
            then round(
                (a.community_centres_count::numeric / nullif(f.population, 0) * 1000)
                / ca.city_avg_commcentres_1k * 100, 1)
            else null
        end                                                                     as amenities_commcentres_index,

        -- ── Amenities: Total ─────────────────────────────────────────────
        a.total_amenities                                                      as amenities,
        a.total_amenities_per_1000                                             as amenities_1k,
        round(ca.city_avg_amenities_1k::numeric, 3)                           as amenities_city_1k,
        case
            when ca.city_avg_amenities_1k > 0
            then round(a.total_amenities_per_1000 / ca.city_avg_amenities_1k * 100, 1)
            else null
        end                                                                     as amenities_index,
        a.amenities_per_sqkm,
        t.amenities_tier,

        -- ── Transit ───────────────────────────────────────────────────────
        a.transit_count,
        a.transit_per_1000                                                     as transit_1k,
        round(ca.city_avg_transit_1k::numeric, 3)                             as transit_city_1k,
        case
            when ca.city_avg_transit_1k > 0
            then round(a.transit_per_1000 / ca.city_avg_transit_1k * 100, 1)
            else null
        end                                                                     as transit_index,

        -- ── Commute Mode (raw counts) ─────────────────────────────────────
        a.commute_car,
        a.commute_car_driver,
        a.commute_car_passenger,
        a.commute_transit,
        a.commute_walk,
        a.commute_bicycle,
        a.commute_outside_canada,
        a.commute_usual_workplace,
        a.commute_work_from_home,
        a.commute_no_fixed_address,
        a.commute_other,

        -- ── Commute Mode (percentages) ────────────────────────────────────
        a.car_dependency_pct,
        round(
            coalesce(a.commute_car, 0)::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        )                                                                       as commute_car_pct,
        round(
            coalesce(a.commute_transit, 0)::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        )                                                                       as commute_transit_pct,
        round(
            (coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0))::numeric
            / nullif(
                coalesce(a.commute_car, 0) + coalesce(a.commute_transit, 0)
                + coalesce(a.commute_walk, 0) + coalesce(a.commute_bicycle, 0)
                + coalesce(a.commute_other, 0),
                0
            ) * 100, 2
        )                                                                       as commute_active_pct,

        -- ── Commute Duration ─────────────────────────────────────────────
        a.commute_under_15min,
        a.commute_15_29min,
        a.commute_30_44min,
        a.commute_45_59min,
        a.commute_60min_plus                                                   as commute_above_60min,
        round(
            (coalesce(a.commute_45_59min, 0) + coalesce(a.commute_60min_plus, 0))::numeric
            / nullif(
                coalesce(a.commute_under_15min, 0) + coalesce(a.commute_15_29min, 0)
                + coalesce(a.commute_30_44min, 0) + coalesce(a.commute_45_59min, 0)
                + coalesce(a.commute_60min_plus, 0),
                0
            ) * 100, 2
        )                                                                       as commute_long_pct

    from neighbourhoods n
    join foundation_all f using (neighbourhood_id)
    join amenity_latest a using (neighbourhood_id)
    join amenity_tiers t using (neighbourhood_id)
    join city_avg ca on ca.census_year = f.census_year
)

select * from final
