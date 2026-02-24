-- Sprint 12 Phase 1 Migration: Raw Layer Foundation
-- Adds category_total and indent_level to fact_neighbourhood_profile
-- Creates fact_census_extended table
--
-- Run BEFORE re-running ETL (make load-toronto).
-- Safe to run multiple times (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).

-- ============================================================
-- 1. Add new columns to fact_neighbourhood_profile
-- ============================================================

ALTER TABLE raw_toronto.fact_neighbourhood_profile
    ADD COLUMN IF NOT EXISTS category_total INTEGER,
    ADD COLUMN IF NOT EXISTS indent_level SMALLINT NOT NULL DEFAULT 0;

-- New composite index for denominator lookups
CREATE INDEX IF NOT EXISTS ix_fact_profile_indent
    ON raw_toronto.fact_neighbourhood_profile (neighbourhood_id, category, indent_level);

-- ============================================================
-- 2. Create fact_census_extended (Path B wide scalar indicators)
-- ============================================================

CREATE TABLE IF NOT EXISTS raw_toronto.fact_census_extended (
    id                            SERIAL PRIMARY KEY,
    neighbourhood_id              INTEGER NOT NULL,
    census_year                   INTEGER NOT NULL,
    -- Population
    population                    INTEGER,
    pop_0_to_14                   INTEGER,
    pop_15_to_24                  INTEGER,
    pop_25_to_64                  INTEGER,
    pop_65_plus                   INTEGER,
    -- Households
    total_private_dwellings       INTEGER,
    occupied_private_dwellings    INTEGER,
    avg_household_size            NUMERIC(6, 2),
    avg_household_income_after_tax NUMERIC(12, 2),
    -- Housing
    pct_owner_occupied            NUMERIC(5, 2),
    pct_renter_occupied           NUMERIC(5, 2),
    pct_suitable_housing          NUMERIC(5, 2),
    avg_shelter_cost_owner        NUMERIC(10, 2),
    avg_shelter_cost_renter       NUMERIC(10, 2),
    pct_shelter_cost_30pct        NUMERIC(5, 2),
    -- Education
    pct_no_certificate            NUMERIC(5, 2),
    pct_high_school               NUMERIC(5, 2),
    pct_college                   NUMERIC(5, 2),
    pct_university                NUMERIC(5, 2),
    pct_postsecondary             NUMERIC(5, 2),
    -- Labour
    participation_rate            NUMERIC(5, 2),
    employment_rate               NUMERIC(5, 2),
    unemployment_rate             NUMERIC(5, 2),
    pct_employed_full_time        NUMERIC(5, 2),
    -- Income
    median_after_tax_income       NUMERIC(12, 2),
    median_employment_income      NUMERIC(12, 2),
    lico_at_rate                  NUMERIC(5, 2),
    market_basket_measure_rate    NUMERIC(5, 2),
    -- Diversity
    pct_immigrants                NUMERIC(5, 2),
    pct_recent_immigrants         NUMERIC(5, 2),
    pct_visible_minority          NUMERIC(5, 2),
    pct_indigenous                NUMERIC(5, 2),
    -- Language
    pct_english_only              NUMERIC(5, 2),
    pct_french_only               NUMERIC(5, 2),
    pct_neither_official_lang     NUMERIC(5, 2),
    pct_bilingual                 NUMERIC(5, 2),
    -- Mobility
    pct_non_movers                NUMERIC(5, 2),
    pct_movers_within_city        NUMERIC(5, 2),
    pct_movers_from_other_city    NUMERIC(5, 2),
    -- Commuting
    pct_car_commuters             NUMERIC(5, 2),
    pct_transit_commuters         NUMERIC(5, 2),
    pct_active_commuters          NUMERIC(5, 2),
    pct_work_from_home            NUMERIC(5, 2),
    -- Additional indicators
    median_age                    NUMERIC(5, 2),
    pct_lone_parent_families      NUMERIC(5, 2),
    avg_number_of_children        NUMERIC(5, 2),
    pct_dwellings_in_need_of_repair NUMERIC(5, 2),
    pct_unaffordable_housing      NUMERIC(5, 2),
    pct_overcrowded_housing       NUMERIC(5, 2),
    median_commute_minutes        NUMERIC(5, 1),
    pct_management_occupation     NUMERIC(5, 2),
    pct_business_finance_admin    NUMERIC(5, 2),
    pct_service_sector            NUMERIC(5, 2),
    pct_trades_transport          NUMERIC(5, 2),
    population_density            NUMERIC(10, 2),
    -- Constraints
    CONSTRAINT uq_fact_census_extended_natural_key
        UNIQUE (neighbourhood_id, census_year)
);

CREATE INDEX IF NOT EXISTS ix_fact_census_extended_nbhd_year
    ON raw_toronto.fact_census_extended (neighbourhood_id, census_year);

-- ============================================================
-- Verification queries (run after ETL to validate)
-- ============================================================
-- SELECT count(*) FROM raw_toronto.fact_neighbourhood_profile;
--   Expected: ~55,000+
-- SELECT count(*) FROM raw_toronto.fact_census_extended;
--   Expected: 158
-- SELECT count(*) FROM raw_toronto.fact_neighbourhood_profile
--   WHERE indent_level IS NULL;
--   Expected: 0
-- SELECT count(*) FROM raw_toronto.fact_neighbourhood_profile
--   WHERE category_total IS NOT NULL;
--   Expected: > 0 (section header rows)
