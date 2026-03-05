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

**In-scope leagues (7):** Premier League (GB1), La Liga (ES1), Bundesliga (L1), Serie A (IT1), Ligue 1 (FR1), Brasileirao (BRA1), MLS (MLS1)

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

#### `mart_neighbourhood_geometry`
Canonical neighbourhood boundaries for map rendering.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `neighbourhood_id` | INTEGER | PK, NOT NULL, UNIQUE | Neighbourhood identifier |
| `neighbourhood_name` | TEXT | NOT NULL | Official neighbourhood name |
| `geometry` | GEOMETRY(MULTIPOLYGON, 4326) | NOT NULL | PostGIS neighbourhood boundary |

**Grain:** 158 rows (one per neighbourhood)
**FK target for:** All analytical Toronto marts via `neighbourhood_id`

#### `mart_neighbourhood_livability`
Grain: neighbourhood × year (2014-2025). Composite livability score and top-level summary metrics.

> Join to `mart_neighbourhood_geometry` via `neighbourhood_id` for name and geometry.

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | FK → mart_neighbourhood_geometry |
| `year` | INTEGER | Analysis year (2014-2025) |
| `population` | INTEGER | Census population (most recent available) |
| `median_household_income` | NUMERIC | CPI-adjusted to 2021 dollars |
| `safety_score` | NUMERIC | Crime rate percentile (0-100, higher = safer) |
| `affordability_score` | NUMERIC | Housing affordability index |
| `amenity_score` | NUMERIC | Amenity accessibility normalized score |
| `livability_score` | NUMERIC | Composite (30% safety + 40% affordability + 30% amenity) |
| `crime_rate_per_100k` | NUMERIC | Raw crime rate per 100,000 |
| `rent_to_income_pct` | NUMERIC | Rental affordability ratio (%) |
| `avg_rent_2bed` | NUMERIC | Average 2-bedroom rent (CAD) |
| `vacancy_rate` | NUMERIC | Rental vacancy percentage |
| `total_amenities_per_1000` | NUMERIC | Density of parks, schools, transit |

**Expected rows:** ~1,738 (158 neighbourhoods × 12 years)

#### `mart_neighbourhood_housing`
Grain: neighbourhood × rental year. Unified housing analysis mart.

**Replaces:** former `mart_neighbourhood_housing` (scalar census-only) + deleted `mart_neighbourhood_housing_rentals` (long format bedroom × year). Bedroom-type metrics are now pivoted to wide format (4 columns per metric).

**Excluded columns** (available in `mart_neighbourhood_people` to avoid duplication): `median_household_income`, `average_dwelling_value`, `income_quintile`, shelter costs, dwelling/bedroom/construction period pivots.

> Join to `mart_neighbourhood_geometry` via `neighbourhood_id` for name and geometry.

**Expected rows:** ~(rental years × 158)

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | FK → mart_neighbourhood_geometry |
| `year` | INTEGER | Rental year |
| `census_year` | INTEGER | Most recent census year ≤ rental year |
| `housing_occupied_owner_pct` | NUMERIC | % dwellings owner-occupied |
| `housing_occupied_renter_pct` | NUMERIC | % dwellings renter-occupied |
| `housing_rent_bachelor_avg` | NUMERIC | Area-weighted avg rent — bachelor units |
| `housing_rent_1bed_avg` | NUMERIC | Area-weighted avg rent — 1-bedroom units |
| `housing_rent_2bed_avg` | NUMERIC | Area-weighted avg rent — 2-bedroom units (primary affordability reference) |
| `housing_rent_3bed_avg` | NUMERIC | Area-weighted avg rent — 3-bedroom units |
| `housing_rent_yoy_bachelor` | NUMERIC | YoY rent change (absolute) — bachelor, from CMHC source |
| `housing_rent_yoy_1bed` | NUMERIC | YoY rent change (absolute) — 1-bed, from CMHC source |
| `housing_rent_yoy_2bed` | NUMERIC | YoY rent change (absolute) — 2-bed, from CMHC source |
| `housing_rent_yoy_3bed` | NUMERIC | YoY rent change (absolute) — 3-bed, from CMHC source |
| `housing_rent_yoy_pct_bachelor` | NUMERIC | YoY rent change % — bachelor (computed from allocated rents) |
| `housing_rent_yoy_pct_1bed` | NUMERIC | YoY rent change % — 1-bed (computed from allocated rents) |
| `housing_rent_yoy_pct_2bed` | NUMERIC | YoY rent change % — 2-bed (computed from allocated rents) |
| `housing_rent_yoy_pct_3bed` | NUMERIC | YoY rent change % — 3-bed (computed from allocated rents) |
| `housing_vacancy_rate_bachelor` | NUMERIC | Area-weighted vacancy rate — bachelor |
| `housing_vacancy_rate_1bed` | NUMERIC | Area-weighted vacancy rate — 1-bed |
| `housing_vacancy_rate_2bed` | NUMERIC | Area-weighted vacancy rate — 2-bed |
| `housing_vacancy_rate_3bed` | NUMERIC | Area-weighted vacancy rate — 3-bed |
| `housing_turnover_rate_bachelor` | NUMERIC | Area-weighted turnover rate — bachelor |
| `housing_turnover_rate_1bed` | NUMERIC | Area-weighted turnover rate — 1-bed |
| `housing_turnover_rate_2bed` | NUMERIC | Area-weighted turnover rate — 2-bed |
| `housing_turnover_rate_3bed` | NUMERIC | Area-weighted turnover rate — 3-bed |
| `housing_rental_universe_est_bachelor` | NUMERIC | Rental universe estimate (area-weighted) — bachelor |
| `housing_rental_universe_est_1bed` | NUMERIC | Rental universe estimate (area-weighted) — 1-bed |
| `housing_rental_universe_est_2bed` | NUMERIC | Rental universe estimate (area-weighted) — 2-bed |
| `housing_rental_universe_est_3bed` | NUMERIC | Rental universe estimate (area-weighted) — 3-bed |
| `housing_rental_units` | NUMERIC | Total rental units (sum across all bedroom types) |
| `housing_rent2income_pct` | NUMERIC | Rent-to-income ratio. Formula: (2bed_avg_rent × 12) / median_income × 100 |
| `housing_affordable` | BOOLEAN | TRUE when 2-bed annual rent ≤ 30% of median household income |
| `housing_affordability_index` | NUMERIC | 100 = city average affordability for the year |
| `housing_affordability_pressure_score` | NUMERIC | Composite 0–100: rent burden (50%) + renter share (30%) + low vacancy (20%) |
| `housing_turnover_rate` | NUMERIC | Turnover rate scalar — 2-bed value (backward-compat single-value reference) |

#### `mart_neighbourhood_people`
Grain: one row per neighbourhood per census year (316 rows: 158 × 2). Unified people profile combining demographics, amenities, commute patterns, and geometry. Replaces deprecated `mart_neighbourhood_demographics` and `mart_neighbourhood_amenities`.

**BREAKING CHANGE (Sprint 16):** grain changed from 158 to 316 rows; `census_year` column added. Webapp queries must filter by `census_year` or aggregate across years.

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | Composite PK with census_year / FK → mart_neighbourhood_geometry |
| `census_year` | INTEGER | Census year (2016 or 2021). Grain key. |
| `neighbourhood_name` | VARCHAR | Official neighbourhood name |
| `geometry` | GEOMETRY | Neighbourhood boundary polygon |
| `land_area_sqkm` | NUMERIC | Land area in square km |
| `pop` | INTEGER | Total population (census year) |
| `pop_density` | NUMERIC | Population per square km |
| `pop_0_to_14` | INTEGER | Population aged 0–14 |
| `pop_15_to_24` | INTEGER | Population aged 15–24 |
| `pop_25_to_64` | INTEGER | Population aged 25–64 |
| `pop_65_plus` | INTEGER | Population aged 65+ |
| `age_md` | NUMERIC | Median age |
| `age_city_avg` | NUMERIC | City-wide average median age |
| `age_index` | NUMERIC | 100 = city average age |
| `edu_bachelors_pct` | NUMERIC | % with bachelor's degree or higher |
| `edu_nonbachelors_pct` | NUMERIC | 100 − edu_bachelors_pct |
| `income_household_md` | NUMERIC | Median household income (CPI-adjusted) |
| `income_household_avg` | NUMERIC | Average household income (CPI-adjusted) |
| `income_quintile` | INTEGER | City-wide quintile (1=lowest, 5=highest) |
| `is_imputed` | BOOLEAN | TRUE for CPI-adjusted 2016–2020 values |
| `income_city_avg` | NUMERIC | City-wide average median income |
| `income_index` | NUMERIC | 100 = city average income |
| `unemployment_rate` | NUMERIC | Neighbourhood unemployment rate |
| `unemployment_city_rate` | NUMERIC | City-wide average unemployment rate |
| `unemployment_index` | NUMERIC | 100 = city average unemployment |
| `housing_occupied_owner` | NUMERIC | % owner-occupied dwellings |
| `housing_occupied_renter` | NUMERIC | % renter-occupied dwellings |
| `housing_dwelling_value_avg` | NUMERIC | Average dwelling value |
| `housing_tenure_diversity_index` | NUMERIC | Herfindahl complement (0=single tenure, ~50=mixed) |
| `amenities_parks` | INTEGER | Raw park count |
| `amenities_parks_1k` | NUMERIC | Parks per 1000 pop |
| `amenities_parks_city_1k` | NUMERIC | City avg parks per 1000 pop |
| `amenities_parks_index` | NUMERIC | 100 = city average |
| `amenities_schools` | INTEGER | Raw school count |
| `amenities_schools_1k` | NUMERIC | Schools per 1000 pop |
| `amenities_schools_city_1k` | NUMERIC | City avg schools per 1000 pop |
| `amenities_schools_index` | NUMERIC | 100 = city average |
| `amenities_libraries` | INTEGER | Raw library count |
| `amenities_libraries_1k` | NUMERIC | Libraries per 1000 pop (computed) |
| `amenities_libraries_city_1k` | NUMERIC | City avg libraries per 1000 pop |
| `amenities_libraries_index` | NUMERIC | 100 = city average |
| `amenities_childcare` | INTEGER | Raw childcare count |
| `amenities_childcare_1k` | NUMERIC | Childcare per 1000 pop (computed) |
| `amenities_childcare_city_1k` | NUMERIC | City avg childcare per 1000 pop |
| `amenities_childcare_index` | NUMERIC | 100 = city average |
| `amenities_commcentres` | INTEGER | Raw community centre count |
| `amenities_commcentres_1k` | NUMERIC | Community centres per 1000 pop (computed) |
| `amenities_commcentres_city_1k` | NUMERIC | City avg community centres per 1000 pop |
| `amenities_commcentres_index` | NUMERIC | 100 = city average |
| `amenities` | INTEGER | Total raw amenity count |
| `amenities_1k` | NUMERIC | Total amenities per 1000 pop |
| `amenities_city_1k` | NUMERIC | City avg total amenities per 1000 pop |
| `amenities_index` | NUMERIC | 100 = city average total amenities |
| `amenities_tier` | INTEGER | Amenity tier 1–5 (1=best) by ntile(5) |
| `amenities_per_sqkm` | NUMERIC | Total amenities per square km |
| `transit_count` | INTEGER | Raw transit stop count |
| `transit_1k` | NUMERIC | Transit stops per 1000 pop |
| `transit_city_1k` | NUMERIC | City avg transit stops per 1000 pop |
| `transit_index` | NUMERIC | 100 = city average transit access |
| `commute_car` | INTEGER | Car commuters (raw count) |
| `commute_car_driver` | INTEGER | Car driver commuters |
| `commute_car_passenger` | INTEGER | Car passenger commuters |
| `commute_transit` | INTEGER | Public transit commuters |
| `commute_walk` | INTEGER | Walking commuters |
| `commute_bicycle` | INTEGER | Bicycle commuters |
| `commute_other` | INTEGER | Other mode commuters |
| `commute_outside_canada` | INTEGER | Worked outside Canada |
| `commute_usual_workplace` | INTEGER | Usual place of work |
| `commute_work_from_home` | INTEGER | Worked at home |
| `commute_no_fixed_address` | INTEGER | No fixed workplace |
| `car_dependency_pct` | NUMERIC | % commuters using car |
| `commute_car_pct` | NUMERIC | % commuters using car |
| `commute_transit_pct` | NUMERIC | % commuters using public transit |
| `commute_active_pct` | NUMERIC | % commuters walking or cycling |
| `commute_under_15min` | INTEGER | < 15 min commuters |
| `commute_15_29min` | INTEGER | 15–29 min commuters |
| `commute_30_44min` | INTEGER | 30–44 min commuters |
| `commute_45_59min` | INTEGER | 45–59 min commuters |
| `commute_above_60min` | INTEGER | 60+ min commuters |
| `commute_long_pct` | NUMERIC | % commuters with 45+ min commute |

**Expected rows:** 316 (158 neighbourhoods × 2 census years)

#### `mart_neighbourhood_safety`
Grain: neighbourhood × year. Crime rate calculations by type.

> Join to `mart_neighbourhood_geometry` via `neighbourhood_id` for name and geometry.

**Expected rows:** varies by available crime years

#### `mart_neighbourhood_profile`
Grain: neighbourhood × census year × category × subcategory. Full community profile breakdown.

| Column | Type | Description |
|--------|------|-------------|
| `neighbourhood_id` | INTEGER | FK → mart_neighbourhood_geometry |
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

> Join to `mart_neighbourhood_geometry` via `neighbourhood_id` for name and geometry.

**Expected rows:** ~108,230

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

*Last Updated: 2026-03-04*
