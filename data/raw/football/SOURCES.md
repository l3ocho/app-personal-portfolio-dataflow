# Football Data Sources

## Primary: salimt/football-datasets (Transfermarkt)

- **GitHub:** https://github.com/salimt/football-datasets
- **Kaggle:** https://www.kaggle.com/datasets/xfkzujqjvx97n/football-datasets
- **Records:** 5.7M+ across all tables
- **Players:** 93,000+
- **Last Updated:** October 2025
- **Coverage:** Player values, transfers, clubs, competitions (Transfermarkt-sourced)

### Setup (git submodule)

```bash
# Register submodule (only needed if .gitmodules was lost)
git submodule add https://github.com/salimt/football-datasets data/raw/football/salimt

# Initialize and clone (standard first-time setup)
git submodule update --init --recursive data/raw/football/salimt

# Update to latest
git -C data/raw/football/salimt pull origin main
```

### Key files (relative to `data/raw/football/salimt/`)

| File | Parser path | Description |
|------|-------------|-------------|
| `team_competitions_seasons/team_competitions_seasons.csv` | `parse_leagues()`, `parse_club_season_stats()` | Competition metadata + club season records |
| `team_details/team_details.csv` | `parse_clubs()` | Club metadata |
| `player_profiles/player_profiles.csv` | `parse_players()` | Player profiles and market values |
| `player_market_value/player_market_value.csv` | `parse_player_market_values()` | Historical market value snapshots |
| `transfer_history/transfer_history.csv` | `parse_transfers()` | Transfer records (Git LFS — large file) |

### Scope filter

Parser filters to 7 leagues: `GB1` (Premier League), `ES1` (La Liga), `L1` (Bundesliga),
`IT1` (Serie A), `FR1` (Ligue 1), `BRA1` (Brasileirão), `MLS1` (MLS).

---

## Secondary: MLSPA Salary Guide (MLS Only)

- **URL:** https://mlsplayers.org/resources/salary-guide
- **Cleaned Dataset:** https://utdata.github.io/mls-salaries/
- **Coverage:** 2007–2025 (official union data, 100% accurate)
- **Update:** Semi-annual (Spring + Fall)

### Setup

Download cleaned CSV files from https://utdata.github.io/mls-salaries/ and place in:

```
data/raw/football/mlspa/
  mls_salaries_<year>.csv      # one file per season or combined
```

Expected columns: `player_id, player_name, club_id, club_name, season, salary_usd, guaranteed_compensation_usd`

---

## Tertiary: Deloitte Football Money League (Revenue)

- **Source:** https://en.wikipedia.org/wiki/Deloitte_Football_Money_League
- **Method:** Wikipedia table scrape (structured HTML tables)
- **Coverage:** Top 20–30 clubs globally, 1996/97 to present
- **Fields extracted:** club name, revenue (€m), season, rank
- **Cache:** `data/raw/football/deloitte/wikipedia_cache.html` (auto-generated on first run)
- **Mapping:** `data/raw/football/deloitte/club_name_mapping.json` (Wikipedia name → Transfermarkt club_id)

**Note:** Only total revenue available via Wikipedia. Matchday/broadcast/commercial breakdown
requires PDF extraction (not implemented).

### Dependencies

```bash
.venv/bin/pip install lxml  # required for BeautifulSoup HTML parser
```

---

## Running the Pipeline

```bash
# Full load (raw + dbt)
make load-football

# Raw only (skip dbt)
make load-football-only

# dbt only (if raw already loaded)
cd dbt && ../.venv/bin/dbt run --select path:models/staging/football path:models/intermediate/football path:models/marts/football
```
