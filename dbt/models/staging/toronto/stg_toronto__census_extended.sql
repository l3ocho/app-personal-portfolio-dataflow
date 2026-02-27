-- Staged census extended scalar indicators
-- Source: raw_toronto.fact_census_extended
-- Grain: One row per (neighbourhood_id, census_year)
-- All indicator columns nullable (Statistics Canada suppression codes)

with source as (
    select * from {{ source('toronto', 'fact_census_extended') }}
),

staged as (
    select
        id                              as census_extended_id,
        neighbourhood_id,
        census_year,

        -- Population
        population,
        pop_0_to_14,
        pop_15_to_24,
        pop_25_to_64,
        pop_65_plus,

        -- Households
        total_private_dwellings,
        occupied_private_dwellings,
        avg_household_size,
        avg_household_income_after_tax,

        -- Housing tenure and costs
        pct_owner_occupied,
        pct_renter_occupied,
        pct_suitable_housing,
        avg_shelter_cost_owner,
        avg_shelter_cost_renter,
        pct_shelter_cost_30pct,

        -- Education
        pct_no_certificate,
        pct_high_school,
        pct_college,
        pct_university,
        pct_postsecondary,

        -- Labour force
        participation_rate,
        employment_rate,
        unemployment_rate,
        pct_employed_full_time,

        -- Income
        median_after_tax_income,
        median_employment_income,
        lico_at_rate,

        -- Diversity / immigration
        pct_immigrants,
        pct_recent_immigrants,
        pct_visible_minority,
        pct_indigenous,

        -- Language
        pct_english_only,
        pct_french_only,
        pct_neither_official_lang,
        pct_bilingual,

        -- Mobility / migration
        pct_non_movers,
        pct_movers_within_city,
        pct_movers_from_other_city,

        -- Commuting / transport
        pct_car_commuters,
        pct_transit_commuters,
        pct_active_commuters,
        pct_work_from_home,

        -- Additional indicators
        median_age,
        pct_lone_parent_families,
        avg_number_of_children,
        pct_dwellings_in_need_of_repair,
        pct_unaffordable_housing,
        pct_overcrowded_housing,
        pct_management_occupation,
        pct_business_finance_admin,
        pct_service_sector,
        pct_trades_transport,
        population_density

    from source
)

select * from staged
