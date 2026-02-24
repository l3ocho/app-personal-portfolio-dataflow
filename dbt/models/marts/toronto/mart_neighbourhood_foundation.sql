-- Mart: Neighbourhood Foundation
-- Dashboard Tab: Foundation
-- Grain: One row per neighbourhood per census year
--
-- Direct surface of int_neighbourhood__foundation.
-- Provides a single complete table for neighbourhood-level demographic,
-- socioeconomic, and census extended indicators.
--
-- Use this mart when you need the full scalar column set.
-- For curated + city-comparison metrics, see mart_neighbourhood_demographics.

with foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

final as (
    select
        -- Identifiers
        neighbourhood_id,
        neighbourhood_name,
        geometry,
        land_area_sqkm,
        census_year,

        -- Core population
        population,
        population_density,

        -- Income (2021 observed; 2016-2020 CPI-imputed)
        median_household_income,
        average_household_income,
        income_quintile,
        is_imputed,

        -- Demographics
        median_age,
        unemployment_rate,
        education_bachelors_pct,
        average_dwelling_value,

        -- Tenure
        pct_owner_occupied,
        pct_renter_occupied,

        -- Extended: age groups
        pop_0_to_14,
        pop_15_to_24,
        pop_25_to_64,
        pop_65_plus,

        -- Extended: households
        total_private_dwellings,
        occupied_private_dwellings,
        avg_household_size,
        avg_household_income_after_tax,

        -- Extended: housing costs
        pct_suitable_housing,
        avg_shelter_cost_owner,
        avg_shelter_cost_renter,
        pct_shelter_cost_30pct,

        -- Extended: education
        pct_no_certificate,
        pct_high_school,
        pct_college,
        pct_university,
        pct_postsecondary,

        -- Extended: labour force
        participation_rate,
        employment_rate,
        pct_employed_full_time,

        -- Extended: income
        median_after_tax_income,
        median_employment_income,
        lico_at_rate,
        market_basket_measure_rate,

        -- Extended: immigration / diversity
        pct_immigrants,
        pct_recent_immigrants,
        pct_visible_minority,
        pct_indigenous,

        -- Extended: language
        pct_english_only,
        pct_french_only,
        pct_neither_official_lang,
        pct_bilingual,

        -- Extended: mobility
        pct_non_movers,
        pct_movers_within_city,
        pct_movers_from_other_city,

        -- Extended: commuting
        pct_car_commuters,
        pct_transit_commuters,
        pct_active_commuters,
        pct_work_from_home,
        median_commute_minutes,

        -- Extended: family / housing quality
        pct_lone_parent_families,
        avg_number_of_children,
        pct_dwellings_in_need_of_repair,
        pct_unaffordable_housing,
        pct_overcrowded_housing,

        -- Extended: occupation
        pct_management_occupation,
        pct_business_finance_admin,
        pct_service_sector,
        pct_trades_transport

    from foundation
)

select * from final
