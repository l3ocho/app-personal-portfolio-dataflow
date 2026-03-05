-- Intermediate: Flat (wide-format) neighbourhood profile
-- Grain: one row per neighbourhood per census_year
-- Source: stg_toronto__profiles (direct — bypasses long-format intermediates)
-- 13 categories pivoted to named scalar columns (count + pct pairs)
-- This replaces the former long-format mart_neighbourhood_profile.
-- Excluded: household_size, marital_status, household_type (not in raw data)
--           visible_minority, religion, dwelling_type, bedrooms,
--           ethnic_origin, mother_tongue, commute_*, occupation,
--           income_bracket, family_type, industry_sector, income_source
--
-- Pct formula: count / MAX(category_total) OVER (PARTITION BY neighbourhood_id,
--              census_year, category) * 100
-- NOTE: category_total is only populated on indent_level=0 (section header) rows.
--       The window MAX propagates it to all rows in the category.

with profiles as (
    select
        neighbourhood_id,
        census_year,
        category,
        subcategory,
        level,
        indent_level,
        count,
        -- Propagate section header total to all rows in the category
        max(category_total) over (
            partition by neighbourhood_id, census_year, category
        ) as cat_total
    from {{ ref('stg_toronto__profiles') }}
    where category in (
        'immigration_status',
        'language_at_home',
        'official_language',
        'citizenship',
        'generation_status',
        'admission_category',
        'place_of_birth',
        'place_of_birth_recent',
        'indigenous_identity',
        'education_level',
        'field_of_study',
        'construction_period',
        'housing_suitability'
    )
),

-- ── immigration_status → imm ──────────────────────────────────────────────
imm as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'immigrants' then count end)
                                                                as profile_imm_immigrant,
        max(case when subcategory = 'immigrants'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_imm_immigrant_pct,
        max(case when subcategory = 'non-immigrants' then count end)
                                                                as profile_imm_nonimmigrant,
        max(case when subcategory = 'non-immigrants'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_imm_nonimmigrant_pct,
        max(case when subcategory = 'non-permanent residents' then count end)
                                                                as profile_imm_nonperm,
        max(case when subcategory = 'non-permanent residents'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_imm_nonperm_pct
    from profiles
    where category = 'immigration_status'
    group by neighbourhood_id, census_year
),

-- ── language_at_home → lang_home ─────────────────────────────────────────
-- Use indent_level = 4 aggregates (official languages, non-official languages)
lang_home as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'official languages' and indent_level = 4
            then count end)                                     as profile_lang_home_official,
        max(case when subcategory = 'official languages' and indent_level = 4
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_lang_home_official_pct,
        max(case when subcategory = 'non-official languages' and indent_level = 4
            then count end)                                     as profile_lang_home_nonofficial,
        max(case when subcategory = 'non-official languages' and indent_level = 4
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_lang_home_nonofficial_pct
    from profiles
    where category = 'language_at_home'
    group by neighbourhood_id, census_year
),

-- ── official_language → offlang ───────────────────────────────────────────
offlang as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'english only' then count end)
                                                                as profile_offlang_english_only,
        max(case when subcategory = 'english only'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_offlang_english_only_pct,
        max(case when subcategory = 'french only' then count end)
                                                                as profile_offlang_french_only,
        max(case when subcategory = 'french only'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_offlang_french_only_pct,
        max(case when subcategory = 'english and french' then count end)
                                                                as profile_offlang_both,
        max(case when subcategory = 'english and french'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_offlang_both_pct,
        max(case when subcategory = 'neither english nor french' then count end)
                                                                as profile_offlang_neither,
        max(case when subcategory = 'neither english nor french'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_offlang_neither_pct
    from profiles
    where category = 'official_language'
    group by neighbourhood_id, census_year
),

-- ── citizenship → citizen ─────────────────────────────────────────────────
citizen as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'canadian citizens' then count end)
                                                                as profile_citizen_canadian,
        max(case when subcategory = 'canadian citizens'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_citizen_canadian_pct,
        max(case when subcategory = 'not canadian citizens' then count end)
                                                                as profile_citizen_not,
        max(case when subcategory = 'not canadian citizens'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_citizen_not_pct
    from profiles
    where category = 'citizenship'
    group by neighbourhood_id, census_year
),

-- ── generation_status → gen ───────────────────────────────────────────────
gen as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'first generation' then count end)
                                                                as profile_gen_1st,
        max(case when subcategory = 'first generation'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_gen_1st_pct,
        max(case when subcategory = 'second generation' then count end)
                                                                as profile_gen_2nd,
        max(case when subcategory = 'second generation'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_gen_2nd_pct,
        max(case when subcategory = 'third generation or more' then count end)
                                                                as profile_gen_3rd_plus,
        max(case when subcategory = 'third generation or more'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_gen_3rd_plus_pct
    from profiles
    where category = 'generation_status'
    group by neighbourhood_id, census_year
),

-- ── admission_category → admission ────────────────────────────────────────
admission as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'economic immigrants' then count end)
                                                                as profile_admission_economic,
        max(case when subcategory = 'economic immigrants'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_admission_economic_pct,
        max(case when subcategory = 'immigrants sponsored by family' then count end)
                                                                as profile_admission_family,
        max(case when subcategory = 'immigrants sponsored by family'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_admission_family_pct,
        max(case when subcategory = 'refugees' then count end)
                                                                as profile_admission_refugee,
        max(case when subcategory = 'refugees'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_admission_refugee_pct,
        max(case when subcategory = 'other immigrants' then count end)
                                                                as profile_admission_other,
        max(case when subcategory = 'other immigrants'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_admission_other_pct
    from profiles
    where category = 'admission_category'
    group by neighbourhood_id, census_year
),

-- ── place_of_birth → pob ──────────────────────────────────────────────────
-- continent-level rows only (level = 'continent'); Canada is treated separately
pob as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'canada' and indent_level = 2
            then count end)                                     as profile_pob_canada,
        max(case when subcategory = 'canada' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_canada_pct,
        max(case when subcategory = 'africa' and level = 'continent'
            then count end)                                     as profile_pob_africa,
        max(case when subcategory = 'africa' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_africa_pct,
        max(case when subcategory = 'americas' and level = 'continent'
            then count end)                                     as profile_pob_americas,
        max(case when subcategory = 'americas' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_americas_pct,
        max(case when subcategory = 'asia' and level = 'continent'
            then count end)                                     as profile_pob_asia,
        max(case when subcategory = 'asia' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_asia_pct,
        max(case when subcategory = 'europe' and level = 'continent'
            then count end)                                     as profile_pob_europe,
        max(case when subcategory = 'europe' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_europe_pct,
        max(case when subcategory = 'oceania and other places of birth'
            then count end)                                     as profile_pob_oceania,
        max(case when subcategory = 'oceania and other places of birth'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_oceania_pct
    from profiles
    where category = 'place_of_birth'
    group by neighbourhood_id, census_year
),

-- ── place_of_birth_recent → pob_recent ────────────────────────────────────
-- Same structure as pob — recent immigrants only
pob_recent as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'canada' and indent_level = 2
            then count end)                                     as profile_pob_recent_canada,
        max(case when subcategory = 'canada' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_canada_pct,
        max(case when subcategory = 'africa' and level = 'continent'
            then count end)                                     as profile_pob_recent_africa,
        max(case when subcategory = 'africa' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_africa_pct,
        max(case when subcategory = 'americas' and level = 'continent'
            then count end)                                     as profile_pob_recent_americas,
        max(case when subcategory = 'americas' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_americas_pct,
        max(case when subcategory = 'asia' and level = 'continent'
            then count end)                                     as profile_pob_recent_asia,
        max(case when subcategory = 'asia' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_asia_pct,
        max(case when subcategory = 'europe' and level = 'continent'
            then count end)                                     as profile_pob_recent_europe,
        max(case when subcategory = 'europe' and level = 'continent'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_europe_pct,
        max(case when subcategory = 'oceania and other'
            then count end)                                     as profile_pob_recent_oceania,
        max(case when subcategory = 'oceania and other'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_pob_recent_oceania_pct
    from profiles
    where category = 'place_of_birth_recent'
    group by neighbourhood_id, census_year
),

-- ── indigenous_identity → indigenous ─────────────────────────────────────
indigenous as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'indigenous identity' and indent_level = 2
            then count end)                                     as profile_indigenous_yes,
        max(case when subcategory = 'indigenous identity' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_indigenous_yes_pct,
        max(case when subcategory = 'non-indigenous identity' and indent_level = 2
            then count end)                                     as profile_indigenous_no,
        max(case when subcategory = 'non-indigenous identity' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_indigenous_no_pct
    from profiles
    where category = 'indigenous_identity'
    group by neighbourhood_id, census_year
),

-- ── education_level → edu_lvl ─────────────────────────────────────────────
-- Use indent_level = 2 for three-tier summary
edu_lvl as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'no certificate, diploma or degree' and indent_level = 2
            then count end)                                     as profile_edu_lvl_nocert,
        max(case when subcategory = 'no certificate, diploma or degree' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_edu_lvl_nocert_pct,
        max(case when subcategory = 'high (secondary) school diploma or equivalency certificate'
            then count end)                                     as profile_edu_lvl_highschool,
        max(case when subcategory = 'high (secondary) school diploma or equivalency certificate'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_edu_lvl_highschool_pct,
        max(case when subcategory = 'postsecondary certificate, diploma or degree' and indent_level = 2
            then count end)                                     as profile_edu_lvl_postsec,
        max(case when subcategory = 'postsecondary certificate, diploma or degree' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_edu_lvl_postsec_pct
    from profiles
    where category = 'education_level'
    group by neighbourhood_id, census_year
),

-- ── field_of_study → fos ─────────────────────────────────────────────────
-- Top 5 by city-wide count at indent_level = 2
fos as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'business, management and public administration' and indent_level = 2
            then count end)                                     as profile_fos_business,
        max(case when subcategory = 'business, management and public administration' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_fos_business_pct,
        max(case when subcategory = 'social and behavioural sciences and law' and indent_level = 2
            then count end)                                     as profile_fos_social_science,
        max(case when subcategory = 'social and behavioural sciences and law' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_fos_social_science_pct,
        max(case when subcategory = 'architecture, engineering, and related trades' and indent_level = 2
            then count end)                                     as profile_fos_engineering,
        max(case when subcategory = 'architecture, engineering, and related trades' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_fos_engineering_pct,
        max(case when subcategory = 'health and related fields' and indent_level = 2
            then count end)                                     as profile_fos_health,
        max(case when subcategory = 'health and related fields' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_fos_health_pct,
        max(case when subcategory = 'humanities' and indent_level = 2
            then count end)                                     as profile_fos_humanities,
        max(case when subcategory = 'humanities' and indent_level = 2
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_fos_humanities_pct
    from profiles
    where category = 'field_of_study'
    group by neighbourhood_id, census_year
),

-- ── construction_period → const ──────────────────────────────────────────
const as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = '1960 or before' then count end)
                                                                as profile_const_pre1960,
        max(case when subcategory = '1960 or before'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_const_pre1960_pct,
        max(case when subcategory = '1961 to 1980' then count end)
                                                                as profile_const_1961_1980,
        max(case when subcategory = '1961 to 1980'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_const_1961_1980_pct,
        max(case when subcategory = '1981 to 1990' then count end)
                                                                as profile_const_1981_1990,
        max(case when subcategory = '1981 to 1990'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_const_1981_1990_pct,
        max(case when subcategory = '1991 to 2000' then count end)
                                                                as profile_const_1991_2000,
        max(case when subcategory = '1991 to 2000'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_const_1991_2000_pct,
        max(case when subcategory in ('2001 to 2005', '2006 to 2010', '2011 to 2015', '2016 to 2021')
            then count end)                                     as profile_const_post2000,
        max(case when subcategory in ('2001 to 2005', '2006 to 2010', '2011 to 2015', '2016 to 2021')
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_const_post2000_pct
    from profiles
    where category = 'construction_period'
    group by neighbourhood_id, census_year
),

-- ── housing_suitability → suit ────────────────────────────────────────────
suit as (
    select
        neighbourhood_id,
        census_year,
        max(case when subcategory = 'suitable' then count end)
                                                                as profile_suit_suitable,
        max(case when subcategory = 'suitable'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_suit_suitable_pct,
        max(case when subcategory = 'not suitable' then count end)
                                                                as profile_suit_not_suitable,
        max(case when subcategory = 'not suitable'
            then round(count::numeric / nullif(cat_total, 0) * 100, 2) end)
                                                                as profile_suit_not_suitable_pct
    from profiles
    where category = 'housing_suitability'
    group by neighbourhood_id, census_year
),

-- ── Spine: all neighbourhoods × census years ─────────────────────────────
spine as (
    select distinct neighbourhood_id, census_year
    from profiles
),

final as (
    select
        s.neighbourhood_id,
        s.census_year,
        -- immigration_status
        imm.profile_imm_immigrant,          imm.profile_imm_immigrant_pct,
        imm.profile_imm_nonimmigrant,       imm.profile_imm_nonimmigrant_pct,
        imm.profile_imm_nonperm,            imm.profile_imm_nonperm_pct,
        -- language_at_home
        lh.profile_lang_home_official,      lh.profile_lang_home_official_pct,
        lh.profile_lang_home_nonofficial,   lh.profile_lang_home_nonofficial_pct,
        -- official_language
        ol.profile_offlang_english_only,    ol.profile_offlang_english_only_pct,
        ol.profile_offlang_french_only,     ol.profile_offlang_french_only_pct,
        ol.profile_offlang_both,            ol.profile_offlang_both_pct,
        ol.profile_offlang_neither,         ol.profile_offlang_neither_pct,
        -- citizenship
        ct.profile_citizen_canadian,        ct.profile_citizen_canadian_pct,
        ct.profile_citizen_not,             ct.profile_citizen_not_pct,
        -- generation_status
        gn.profile_gen_1st,                 gn.profile_gen_1st_pct,
        gn.profile_gen_2nd,                 gn.profile_gen_2nd_pct,
        gn.profile_gen_3rd_plus,            gn.profile_gen_3rd_plus_pct,
        -- admission_category
        ad.profile_admission_economic,      ad.profile_admission_economic_pct,
        ad.profile_admission_family,        ad.profile_admission_family_pct,
        ad.profile_admission_refugee,       ad.profile_admission_refugee_pct,
        ad.profile_admission_other,         ad.profile_admission_other_pct,
        -- place_of_birth
        pb.profile_pob_canada,              pb.profile_pob_canada_pct,
        pb.profile_pob_africa,              pb.profile_pob_africa_pct,
        pb.profile_pob_americas,            pb.profile_pob_americas_pct,
        pb.profile_pob_asia,                pb.profile_pob_asia_pct,
        pb.profile_pob_europe,              pb.profile_pob_europe_pct,
        pb.profile_pob_oceania,             pb.profile_pob_oceania_pct,
        -- place_of_birth_recent
        pr.profile_pob_recent_canada,       pr.profile_pob_recent_canada_pct,
        pr.profile_pob_recent_africa,       pr.profile_pob_recent_africa_pct,
        pr.profile_pob_recent_americas,     pr.profile_pob_recent_americas_pct,
        pr.profile_pob_recent_asia,         pr.profile_pob_recent_asia_pct,
        pr.profile_pob_recent_europe,       pr.profile_pob_recent_europe_pct,
        pr.profile_pob_recent_oceania,      pr.profile_pob_recent_oceania_pct,
        -- indigenous_identity
        ig.profile_indigenous_yes,          ig.profile_indigenous_yes_pct,
        ig.profile_indigenous_no,           ig.profile_indigenous_no_pct,
        -- education_level
        el.profile_edu_lvl_nocert,          el.profile_edu_lvl_nocert_pct,
        el.profile_edu_lvl_highschool,      el.profile_edu_lvl_highschool_pct,
        el.profile_edu_lvl_postsec,         el.profile_edu_lvl_postsec_pct,
        -- field_of_study
        fs.profile_fos_business,            fs.profile_fos_business_pct,
        fs.profile_fos_social_science,      fs.profile_fos_social_science_pct,
        fs.profile_fos_engineering,         fs.profile_fos_engineering_pct,
        fs.profile_fos_health,              fs.profile_fos_health_pct,
        fs.profile_fos_humanities,          fs.profile_fos_humanities_pct,
        -- construction_period
        cp.profile_const_pre1960,           cp.profile_const_pre1960_pct,
        cp.profile_const_1961_1980,         cp.profile_const_1961_1980_pct,
        cp.profile_const_1981_1990,         cp.profile_const_1981_1990_pct,
        cp.profile_const_1991_2000,         cp.profile_const_1991_2000_pct,
        cp.profile_const_post2000,          cp.profile_const_post2000_pct,
        -- housing_suitability
        su.profile_suit_suitable,           su.profile_suit_suitable_pct,
        su.profile_suit_not_suitable,       su.profile_suit_not_suitable_pct
    from spine s
    left join imm       on s.neighbourhood_id = imm.neighbourhood_id and s.census_year = imm.census_year
    left join lang_home lh on s.neighbourhood_id = lh.neighbourhood_id  and s.census_year = lh.census_year
    left join offlang   ol on s.neighbourhood_id = ol.neighbourhood_id  and s.census_year = ol.census_year
    left join citizen   ct on s.neighbourhood_id = ct.neighbourhood_id  and s.census_year = ct.census_year
    left join gen       gn on s.neighbourhood_id = gn.neighbourhood_id  and s.census_year = gn.census_year
    left join admission ad on s.neighbourhood_id = ad.neighbourhood_id  and s.census_year = ad.census_year
    left join pob       pb on s.neighbourhood_id = pb.neighbourhood_id  and s.census_year = pb.census_year
    left join pob_recent pr on s.neighbourhood_id = pr.neighbourhood_id and s.census_year = pr.census_year
    left join indigenous ig on s.neighbourhood_id = ig.neighbourhood_id and s.census_year = ig.census_year
    left join edu_lvl   el on s.neighbourhood_id = el.neighbourhood_id  and s.census_year = el.census_year
    left join fos       fs on s.neighbourhood_id = fs.neighbourhood_id  and s.census_year = fs.census_year
    left join const     cp on s.neighbourhood_id = cp.neighbourhood_id  and s.census_year = cp.census_year
    left join suit      su on s.neighbourhood_id = su.neighbourhood_id  and s.census_year = su.census_year
)

select * from final
