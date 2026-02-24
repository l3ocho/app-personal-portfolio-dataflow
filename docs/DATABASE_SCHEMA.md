# Database Schema

PostgreSQL + PostGIS schema reference for the Portfolio Data Pipeline.

Two domains, two raw schemas, one shared dimension schema, and a full dbt transformation layer producing analytics-ready marts.

---

## Schema Map

| Schema | Layer | Managed By | Purpose |
|--------|-------|------------|---------|
| `public` | Shared dimension | SQLAlchemy | `dim_time` — cross-domain time dimension |
| `raw_toronto` | Raw ingestion | SQLAlchemy | Toronto dimension + fact tables |
| `raw_football` | Raw ingestion | SQLAlchemy | Football dimension + fact tables |
| `stg_toronto` | Staging (views) | dbt | Toronto 1:1 source cleaning |
| `stg_football` | Staging (views) | dbt | Football 1:1 source cleaning |
| `int_toronto` | Intermediate (views) | dbt | Toronto business logic |
| `int_football` | Intermediate (views) | dbt | Football business logic |
| `mart_toronto` | Mart (tables) | dbt | Toronto analytics-ready tables |
| `mart_football` | Mart (tables) | dbt | Football analytics-ready tables |

---

## Raw Toronto Schema (`raw_toronto`)

### Dimension Tables

#### `dim_neighbourhood`
Toronto's 158 official neighbourhoods with PostGIS boundaries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `neighbourhood_id` | INTEGER | PK | City-assigned neighbourhood ID |
| `name` | VARCHAR(100) | NOT NULL | Neighbourhood name |
| `geometry` | GEOMETRY(POLYGON, 4326) | | PostGIS boundary (WGS84) |
| `population` | INTEGER | | Total population |
| `land_area_sqkm` | NUMERIC(10,4) | | Area in km² |
| `pop_density_per_sqkm` | NUMERIC(10,2) | | Population density |
| `pct_bachelors_or_higher` | NUMERIC(5,2) | | Bachelor's degree or higher |
| `median_household_income` | NUMERIC(12,2) | | Median household income |
| `pct_owner_occupied` | NUMERIC(5,2) | | Owner-occupied dwelling rate |
| `pct_renter_occupied` | NUMERIC(5,2) | | Renter-occupied dwelling rate |
| `census_year` | INTEGER | DEFAULT 2021 | Census reference year |

#### `dim_cmhc_zone`
CMHC rental market zones (~36 zones covering the Toronto CMA).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `zone_key` | INTEGER | PK, AUTO | Surrogate key |
| `zone_code` | VARCHAR(10) | UNIQUE, NOT NULL | CMHC zone identifier |
| `zone_name` | VARCHAR(100) | NOT NULL | Zone display name |
| `geometry` | GEOMETRY(POLYGON, 4326) | | PostGIS zone boundary |

#### `dim_policy_event`
Policy events for time-series annotation (rent control, interest rates, etc.).
Table exists but requires manual data curation — deferred to future phase.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `event_id` | INTEGER | PK, AUTO | Surrogate key |
| `event_date` | DATE | NOT NULL | Announcement date |
| `effective_date` | DATE | | Implementation date |
| `level` | VARCHAR(20) | NOT NULL | `federal` / `provincial` / `municipal` |
| `category` | VARCHAR(20) | NOT NULL | `monetary` / `tax` / `regulatory` / `supply` / `economic` |
| `title` | VARCHAR(200) | NOT NULL | Event title |
| `description` | TEXT | | Detailed description |
| `expected_direction` | VARCHAR(10) | NOT NULL | `bearish` / `bullish` / `neutral` |
| `source_url` | VARCHAR(500) | | Reference link |
| `confidence` | VARCHAR(10) | DEFAULT 'medium' | `high` / `medium` / `low` |

---

### Fact Tables

#### `fact_census`
Core census statistics. Grain: neighbourhood × census year.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Surrogate key |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood | Neighbourhood reference |
| `census_year` | INTEGER | NOT NULL | 2016, 2021 |
| `population` | INTEGER | | Total population |
| `population_density` | NUMERIC(10,2) | | People per km² |
| `median_household_income` | NUMERIC(12,2) | | ⚠️ NULL for 2016 — see note below |
| `average_household_income` | NUMERIC(12,2) | | ⚠️ NULL for 2016 — see note below |
| `unemployment_rate` | NUMERIC(5,2) | | Unemployment % |
| `pct_bachelors_or_higher` | NUMERIC(5,2) | | Education rate |
| `pct_owner_occupied` | NUMERIC(5,2) | | Owner rate |
| `pct_renter_occupied` | NUMERIC(5,2) | | Renter rate |
| `median_age` | NUMERIC(5,2) | | Median resident age |
| `average_dwelling_value` | NUMERIC(12,2) | | Average home value |

> **Income note:** The 2016 Toronto Open Data census does not include neighbourhood-level income. `median_household_income` and `average_household_income` are NULL for 2016 rows. Downstream dbt models impute 2016 values using CPI backward-adjustment from 2021: `income_2016 = income_2021 × (128.4 / 141.6)`. Imputed values are flagged with `is_imputed = TRUE` in mart models.

---

#### `fact_census_extended`
Wide-format scalar indicators per neighbourhood from the Statistics Canada 2021 Neighbourhood Profile XLSX. Grain: neighbourhood × census year.

Used as the primary source for `int_neighbourhood__foundation`, providing ~55 scalar columns that replace complex profile pivots.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Surrogate key |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood |
| `census_year` | INTEGER | Census reference year |
| **Population** | | |
| `population` | INTEGER | Total population |
| `pop_0_to_14` | INTEGER | Population aged 0–14 |
| `pop_15_to_24` | INTEGER | Population aged 15–24 |
| `pop_25_to_64` | INTEGER | Population aged 25–64 |
| `pop_65_plus` | INTEGER | Population aged 65+ |
| **Households** | | |
| `total_private_dwellings` | INTEGER | Total private dwellings |
| `occupied_private_dwellings` | INTEGER | Occupied private dwellings |
| `avg_household_size` | NUMERIC(6,2) | Average household size |
| `avg_household_income_after_tax` | NUMERIC(12,2) | Average after-tax household income |
| **Housing tenure and costs** | | |
| `pct_owner_occupied` | NUMERIC(5,2) | Owner-occupied % |
| `pct_renter_occupied` | NUMERIC(5,2) | Renter-occupied % |
| `pct_suitable_housing` | NUMERIC(5,2) | Suitable housing % |
| `avg_shelter_cost_owner` | NUMERIC(10,2) | Average monthly shelter cost (owners) |
| `avg_shelter_cost_renter` | NUMERIC(10,2) | Average monthly shelter cost (renters) |
| `pct_shelter_cost_30pct` | NUMERIC(5,2) | Spending 30%+ of income on shelter |
| **Education** | | |
| `pct_no_certificate` | NUMERIC(5,2) | No certificate/diploma/degree |
| `pct_high_school` | NUMERIC(5,2) | High school diploma |
| `pct_college` | NUMERIC(5,2) | College/CEGEP/trades certificate |
| `pct_university` | NUMERIC(5,2) | University degree |
| `pct_postsecondary` | NUMERIC(5,2) | Any post-secondary credential |
| **Labour Force** | | |
| `participation_rate` | NUMERIC(5,2) | Labour force participation rate |
| `employment_rate` | NUMERIC(5,2) | Employment rate |
| `unemployment_rate` | NUMERIC(5,2) | Unemployment rate |
| `pct_employed_full_time` | NUMERIC(5,2) | Full-time employment % |
| **Income** | | |
| `median_after_tax_income` | NUMERIC(12,2) | Median after-tax individual income |
| `median_employment_income` | NUMERIC(12,2) | Median employment income |
| `lico_at_rate` | NUMERIC(5,2) | Low-income (LICO-AT) rate |
| `market_basket_measure_rate` | NUMERIC(5,2) | Market Basket Measure poverty rate |
| **Diversity / Immigration** | | |
| `pct_immigrants` | NUMERIC(5,2) | Immigrants % |
| `pct_recent_immigrants` | NUMERIC(5,2) | Recent immigrants (2016–2021) % |
| `pct_visible_minority` | NUMERIC(5,2) | Visible minority % |
| `pct_indigenous` | NUMERIC(5,2) | Indigenous identity % |
| **Language** | | |
| `pct_english_only` | NUMERIC(5,2) | English only |
| `pct_french_only` | NUMERIC(5,2) | French only |
| `pct_neither_official_lang` | NUMERIC(5,2) | Neither official language |
| `pct_bilingual` | NUMERIC(5,2) | English and French |
| **Mobility** | | |
| `pct_non_movers` | NUMERIC(5,2) | Lived at same address 5 years ago |
| `pct_movers_within_city` | NUMERIC(5,2) | Moved within city |
| `pct_movers_from_other_city` | NUMERIC(5,2) | Moved from another city |
| **Commuting** | | |
| `pct_car_commuters` | NUMERIC(5,2) | Car/truck/van commuters |
| `pct_transit_commuters` | NUMERIC(5,2) | Public transit commuters |
| `pct_active_commuters` | NUMERIC(5,2) | Walking/cycling commuters |
| `pct_work_from_home` | NUMERIC(5,2) | Work from home |
| `median_commute_minutes` | NUMERIC(5,1) | Median commute duration |
| **Additional Indicators** | | |
| `median_age` | NUMERIC(5,2) | Median age |
| `pct_lone_parent_families` | NUMERIC(5,2) | Lone-parent families % |
| `avg_number_of_children` | NUMERIC(5,2) | Average children per family |
| `pct_dwellings_in_need_of_repair` | NUMERIC(5,2) | Dwellings in need of major repair |
| `pct_unaffordable_housing` | NUMERIC(5,2) | Spending 30%+ on shelter |
| `pct_overcrowded_housing` | NUMERIC(5,2) | More than 1 person per room |
| `population_density` | NUMERIC(10,2) | Population per km² |
| `pct_management_occupation` | NUMERIC(5,2) | Management occupations % |
| `pct_business_finance_admin` | NUMERIC(5,2) | Business/finance/admin occupations % |
| `pct_service_sector` | NUMERIC(5,2) | Service sector occupations % |
| `pct_trades_transport` | NUMERIC(5,2) | Trades and transport occupations % |

**Constraints:**
- UNIQUE `(neighbourhood_id, census_year)` — natural key
- INDEX `(neighbourhood_id, census_year)` — primary query pattern

---

#### `fact_neighbourhood_profile`
Community profile data from Statistics Canada. Grain: neighbourhood × census year × category × subcategory × level × indent_level.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | Surrogate key |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood | Neighbourhood reference |
| `census_year` | INTEGER | NOT NULL | 2021 |
| `category` | VARCHAR(50) | NOT NULL | 22 categories — see below |
| `subcategory` | VARCHAR(100) | NOT NULL | Category value (e.g., "South Asian", "English") |
| `count` | INTEGER | NULL allowed | NULL = StatCan suppressed small population |
| `level` | VARCHAR(20) | NOT NULL, DEFAULT '' | `''` / `'continent'` / `'country'` (place_of_birth only) |
| `category_total` | INTEGER | NULL allowed | Section header total — denominator for % calculations |
| `indent_level` | SMALLINT | NOT NULL, DEFAULT 0 | Hierarchy depth from XLSX leading whitespace (0 = top level) |

**Profile Categories (22):**
`immigration_status`, `visible_minority`, `mother_tongue`, `official_language`, `citizenship`, `generation_status`, `admission_category`, `place_of_birth`, `place_of_birth_recent`, `ethnic_origin`, `religion`, `education_level`, `field_of_study`, `commute_mode`, `commute_duration`, `commute_destination`, `housing_suitability`, `dwelling_type`, `bedrooms`, `construction_period`, `indigenous_identity`, `mother_tongue` (expanded)

**Indexes:**
- `(neighbourhood_id, census_year, category)` — primary query pattern
- `(category, subcategory)` — city-wide aggregation
- `(neighbourhood_id, category, indent_level)` — hierarchy traversal
- UNIQUE `(neighbourhood_id, census_year, category, subcategory, level, indent_level)` — natural key

**Data characteristics:**
- ~108,000+ rows total
- `indent_level` required in unique constraint: same subcategory text can appear at multiple hierarchy depths
- `category_total` sourced from XLSX section header rows (used as denominator via `MAX(category_total)` in dbt, not `SUM(count)`)

---

#### `fact_crime`
Crime statistics by neighbourhood. Grain: neighbourhood × year × crime type.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood | |
| `year` | INTEGER | NOT NULL | Calendar year |
| `crime_type` | VARCHAR(50) | NOT NULL | Crime category |
| `count` | INTEGER | NOT NULL | Incident count |
| `rate_per_100k` | NUMERIC(10,2) | | Rate per 100,000 population |

#### `fact_amenities`
Amenity counts. Grain: neighbourhood × amenity type × year.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood | |
| `amenity_type` | VARCHAR(50) | NOT NULL | parks / schools / transit / etc. |
| `count` | INTEGER | NOT NULL | Number of amenities |
| `year` | INTEGER | NOT NULL | Reference year |

#### `fact_rentals`
CMHC rental market survey data. Grain: zone × bedroom type × survey date.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | |
| `date_key` | INTEGER | FK → dim_time | Survey date reference |
| `zone_key` | INTEGER | FK → dim_cmhc_zone | CMHC zone reference |
| `bedroom_type` | VARCHAR(20) | NOT NULL | bachelor / 1-bed / 2-bed / 3+bed / total |
| `universe` | INTEGER | | Total rental units |
| `avg_rent` | NUMERIC(10,2) | | Average rent |
| `vacancy_rate` | NUMERIC(5,2) | | Vacancy % |
| `turnover_rate` | NUMERIC(5,2) | | Turnover % |
| `rent_change_pct` | NUMERIC(5,2) | | Year-over-year change |
| `reliability_code` | VARCHAR(2) | | CMHC data quality code: a/b/c/d |

---

### Bridge Tables

#### `bridge_cmhc_neighbourhood`
Area-weighted mapping between CMHC zones and Toronto neighbourhoods. Used to disaggregate zone-grain rental data to neighbourhood grain.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PK, AUTO | |
| `cmhc_zone_code` | VARCHAR(10) | FK → dim_cmhc_zone | Zone reference |
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood | Neighbourhood reference |
| `weight` | NUMERIC(5,4) | NOT NULL | Proportional area weight (0–1, sums to 1 per zone) |

---

## Public Schema

#### `dim_time`
Shared monthly time dimension. Grain: one row per month.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `date_key` | INTEGER | PK | YYYYMM format (e.g., 202101) |
| `full_date` | DATE | UNIQUE, NOT NULL | First day of month |
| `year` | INTEGER | NOT NULL | Calendar year |
| `month` | INTEGER | NOT NULL | Month number (1–12) |
| `quarter` | INTEGER | NOT NULL | Quarter (1–4) |
| `month_name` | VARCHAR(20) | NOT NULL | Month name |
| `is_month_start` | BOOLEAN | DEFAULT TRUE | Always true (monthly grain) |

---

## Raw Football Schema (`raw_football`)

### Dimension Tables

#### `dim_league`
Football league dimension. Grain: one row per league (static).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `league_id` | VARCHAR(10) | PK | League identifier |
| `league_name` | VARCHAR(100) | NOT NULL | Full league name |
| `country` | VARCHAR(50) | NOT NULL | Country |
| `season_start_year` | INTEGER | NOT NULL | Current season start year |

**In-scope leagues (7):** Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Eredivisie, MLS

#### `dim_club`
Football club dimension. Grain: one row per club (static).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `club_id` | VARCHAR(20) | PK | Transfermarkt club identifier |
| `club_name` | VARCHAR(150) | NOT NULL | Club name |
| `country` | VARCHAR(50) | | Country |
| `club_slug` | VARCHAR(150) | | URL slug |
| `logo_url` | VARCHAR(255) | | Logo URL |
| `source_url` | VARCHAR(255) | | Transfermarkt source URL |

#### `dim_player`
Football player dimension. Grain: one row per player (static).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `player_id` | VARCHAR(20) | PK | Transfermarkt player identifier |
| `player_name` | VARCHAR(150) | NOT NULL | Player name |
| `date_of_birth` | DATE | | Date of birth |
| `nationality` | VARCHAR(50) | | Primary nationality |
| `height_cm` | INTEGER | | Height in centimetres |
| `position` | VARCHAR(50) | | Playing position |
| `preferred_foot` | VARCHAR(10) | | Left / Right |

---

### Fact Tables

#### `fact_player_market_value`
Player market value snapshots. Grain: player × market value date.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `player_id` | VARCHAR(20) | FK → dim_player |
| `club_id` | VARCHAR(20) | FK → dim_club (at time of snapshot) |
| `value_eur` | INTEGER | Market value in EUR |
| `market_value_date` | DATE | Snapshot date |
| `season` | INTEGER | Season year |

#### `fact_transfer`
Transfer history. Grain: one row per transfer event.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `player_id` | VARCHAR(20) | FK → dim_player |
| `from_club_id` | VARCHAR(20) | Source club |
| `to_club_id` | VARCHAR(20) | Destination club |
| `transfer_date` | DATE | Transfer date |
| `fee_eur` | INTEGER | Transfer fee in EUR (NULL = free/loan/unknown) |
| `is_loan` | BOOLEAN | Loan transfer flag |
| `season` | INTEGER | Season year |

#### `fact_club_season`
Club season statistics. Grain: club × league × season.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `club_id` | VARCHAR(20) | FK → dim_club |
| `league_id` | VARCHAR(10) | FK → dim_league |
| `season` | INTEGER | Season start year |
| `position` | INTEGER | Final league position |
| `matches_played` | INTEGER | |
| `wins` / `draws` / `losses` | INTEGER | |
| `goals_for` / `goals_against` | INTEGER | |
| `points` | INTEGER | |

#### `fact_mls_salary`
MLS player salary data. Grain: player × club × season.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `player_id` | VARCHAR(20) | FK → dim_player |
| `player_name` | VARCHAR(150) | Denormalized |
| `club_id` | VARCHAR(20) | FK → dim_club |
| `club_name` | VARCHAR(100) | Denormalized |
| `season` | INTEGER | Season year |
| `salary_usd` | INTEGER | Base salary in USD |
| `guaranteed_compensation_usd` | INTEGER | Guaranteed compensation in USD |

#### `fact_club_finance`
Club annual revenue (Deloitte Money League). Grain: club × season.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `club_id` | VARCHAR(20) | FK → dim_club |
| `club_name` | VARCHAR(150) | Denormalized |
| `season` | INTEGER | Season year |
| `revenue_eur` | INTEGER | Total revenue in EUR |
| `operating_profit_eur` | INTEGER | Operating profit in EUR |

---

### Bridge Tables

#### `bridge_player_competition`
Player-league participation. Grain: player × league × season.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `player_id` | VARCHAR(20) | FK → dim_player |
| `league_id` | VARCHAR(10) | FK → dim_league |
| `season` | INTEGER | Season year |
| `appearances` | INTEGER | League appearances |
| `goals` | INTEGER | Goals scored |
| `assists` | INTEGER | Assists |

---

## Indexes

### Toronto Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `fact_rentals` | `ix_fact_rentals_date_zone` | date_key, zone_key | Time-series queries |
| `fact_census` | `ix_fact_census_neighbourhood_year` | neighbourhood_id, census_year | Census lookups |
| `fact_census_extended` | `ix_fact_census_extended_nbhd_year` | neighbourhood_id, census_year | Extended census lookups |
| `fact_crime` | `ix_fact_crime_neighbourhood_year` | neighbourhood_id, year | Crime trends |
| `fact_crime` | `ix_fact_crime_type` | crime_type | Crime filtering |
| `fact_amenities` | `ix_fact_amenities_neighbourhood_year` | neighbourhood_id, year | Amenity queries |
| `fact_amenities` | `ix_fact_amenities_type` | amenity_type | Amenity filtering |
| `fact_neighbourhood_profile` | `ix_fact_profile_nbhd_year_cat` | neighbourhood_id, census_year, category | Profile queries |
| `fact_neighbourhood_profile` | `ix_fact_profile_cat_subcat` | category, subcategory | City-wide aggregation |
| `fact_neighbourhood_profile` | `ix_fact_profile_indent` | neighbourhood_id, category, indent_level | Hierarchy traversal |
| `bridge_cmhc_neighbourhood` | `ix_bridge_cmhc_zone` | cmhc_zone_code | Zone lookups |
| `bridge_cmhc_neighbourhood` | `ix_bridge_neighbourhood` | neighbourhood_id | Neighbourhood lookups |

### Football Indexes

| Table | Index | Columns |
|-------|-------|---------|
| `fact_player_market_value` | `ix_fact_pmv_player_date` | player_id, market_value_date |
| `fact_player_market_value` | `ix_fact_pmv_club` | club_id |
| `fact_player_market_value` | `ix_fact_pmv_season` | season |
| `fact_transfer` | `ix_fact_transfer_player_date` | player_id, transfer_date |
| `fact_transfer` | `ix_fact_transfer_from_club` | from_club_id |
| `fact_transfer` | `ix_fact_transfer_to_club` | to_club_id |
| `fact_club_season` | `ix_fact_cs_club_season` | club_id, season |
| `fact_mls_salary` | `ix_fact_mls_player_season` | player_id, season |
| `fact_club_finance` | `ix_fact_cf_club_season` | club_id, season |

---

## Mart Tables

Mart tables are the **read-only contract** between this pipeline and the webapp. Column names and types must not change without coordinating with the `personal-portfolio` webapp repository.

### Toronto Marts (`mart_toronto`)

#### `mart_neighbourhood_overview`
Grain: neighbourhood. Composite livability score and top-level summary metrics.

#### `mart_neighbourhood_foundation`
Grain: neighbourhood × census year. The canonical cross-domain base mart.

Includes 65+ columns across: population, age structure, household metrics, after-tax income, employment, education, housing costs and tenure, diversity/immigration, language, commuting, and housing quality indicators. Sources from `int_neighbourhood__foundation`.

**Expected rows:** ~316 (158 neighbourhoods × 2 census years)

#### `mart_neighbourhood_housing`
Grain: neighbourhood × census year. Comprehensive housing analysis (75+ columns).

Includes: dwelling type pivots (7 types), bedroom count pivots (5 sizes), construction period pivots (8 buckets), shelter cost scalars, affordability rates, composite fit scores (`family_housing_fit`, `couple_housing_fit`, `singles_housing_fit`).

**Expected rows:** ~316

#### `mart_neighbourhood_housing_rentals`
Grain: neighbourhood × bedroom type × year. CMHC rental data disaggregated from CMHC zones to neighbourhood grain via area-weighted crosswalk.

Replaces the deprecated `mart_toronto_rentals` (zone grain).

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | FK → dim_neighbourhood |
| `neighbourhood_name` | VARCHAR | Denormalized |
| `bedroom_type` | VARCHAR | bachelor / 1-bed / 2-bed / 3+bed / total |
| `year` | INTEGER | Survey year |
| `avg_rent` | NUMERIC | Area-weighted average rent |
| `vacancy_rate` | NUMERIC | Area-weighted vacancy rate |
| `universe` | INTEGER | Estimated unit count |
| `cmhc_zone_codes` | TEXT | Contributing CMHC zones |
| `geometry` | GEOMETRY | PostGIS neighbourhood boundary |

**Expected rows:** ~4,424

#### `mart_neighbourhood_demographics`
Grain: neighbourhood × census year. Income, age, population, diversity indices, and community profile summary columns (45+ columns).

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | PK |
| `neighbourhood_name` | VARCHAR | |
| `geometry` | GEOMETRY(MULTIPOLYGON, 4326) | |
| `year` | INTEGER | PK |
| `population` | INTEGER | |
| `land_area_sqkm` | NUMERIC | |
| `population_density` | NUMERIC | |
| `median_household_income` | NUMERIC | CPI-adjusted to 2021 dollars |
| `average_household_income` | NUMERIC | CPI-adjusted to 2021 dollars |
| `income_quintile` | INTEGER | 1–5 (1 = lowest) |
| `is_imputed` | BOOLEAN | TRUE for 2016–2020 income values |
| `income_index` | NUMERIC | 100 = city average |
| `median_age` | NUMERIC | |
| `unemployment_rate` | NUMERIC | |
| `education_bachelors_pct` | NUMERIC | |
| `age_index` | NUMERIC | 100 = city average |
| `pct_owner_occupied` | NUMERIC | |
| `pct_renter_occupied` | NUMERIC | |
| `average_dwelling_value` | NUMERIC | |
| `tenure_diversity_index` | NUMERIC | Shannon entropy on owner/renter split |
| `pct_immigrant` | NUMERIC(5,2) | Immigrants % (from profile categories) |
| `pct_visible_minority` | NUMERIC(5,2) | Visible minority % |
| `pct_neither_official_lang` | NUMERIC(5,2) | Neither English nor French % |
| `diversity_index` | NUMERIC(6,4) | Shannon entropy on visible minority composition |

**Expected rows:** ~316

#### `mart_neighbourhood_safety`
Grain: neighbourhood × year. Crime rate calculations by type.

**Expected rows:** varies by available crime years

#### `mart_neighbourhood_amenities`
Grain: neighbourhood. Amenity accessibility scores, commute mode/duration/destination pivots, car dependency index (35+ columns).

Commute pivots sourced from `fact_neighbourhood_profile` profile categories: commute_mode (6 modes), commute_duration (5 buckets), commute_destination (4 destinations). `car_dependency_index` is a composite score.

#### `mart_neighbourhood_profile`
Grain: neighbourhood × census year × category × subcategory. Full community profile breakdown with geometry for map-based analysis.

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | |
| `neighbourhood_name` | VARCHAR | |
| `census_year` | INTEGER | |
| `category` | VARCHAR | One of the 22 profile categories |
| `subcategory` | VARCHAR | |
| `count` | INTEGER | NULL = StatCan suppressed |
| `pct_of_neighbourhood` | NUMERIC(5,2) | % within neighbourhood category total |
| `city_total` | INTEGER | City-wide count for category-subcategory |
| `pct_of_city` | NUMERIC(5,2) | % of city total |
| `rank_in_neighbourhood` | INTEGER | Rank within neighbourhood category |
| `level` | VARCHAR | `''` / `'continent'` / `'country'` |
| `indent_level` | SMALLINT | Hierarchy depth |
| `category_total` | INTEGER | Section header total (denominator) |
| `is_subtotal` | BOOLEAN | TRUE if indent_level > 0 |
| `diversity_index` | NUMERIC(6,4) | Shannon entropy (visible_minority only) |
| `geometry` | GEOMETRY(MULTIPOLYGON, 4326) | PostGIS neighbourhood boundary |

**Expected rows:** ~32,706

---

### Football Marts (`mart_football`)

#### `mart_football_club_rankings`
Club rankings across leagues: squad value, season performance, financial metrics.

#### `mart_football_club_deep_dive`
Per-club detailed analysis: player roster, transfer history, market value trajectory.

#### `mart_football_league_comparison`
Cross-league comparison for the 7 in-scope leagues: aggregate squad values, total revenue, transfer activity.

---

## PostGIS

The database requires PostGIS for geospatial operations:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

All geometry columns use **SRID 4326 (WGS84)** for compatibility with web mapping libraries. Neighbourhood boundaries are stored as `GEOMETRY(MULTIPOLYGON, 4326)` in mart tables, `GEOMETRY(POLYGON, 4326)` in raw dimension tables.

---

*Last Updated: 2026-02-24*
