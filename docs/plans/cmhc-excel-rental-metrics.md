# Plan: Extend CMHC Excel Parser for Rental Metrics

## Problem
`mart_neighbourhood_housing_rentals` (formerly `mart_toronto_rentals`) has several NULL columns. The RMR Excel files
(`data/raw/cmhc/rmr-toronto-{year}-en.xlsx`, years 2021–2025) already on disk
contain the missing data in additional tables beyond the currently-parsed 3.1.3.

## What the Excel files contain

All files share Section 3 (Combined Apt + Townhouse), which is what the
existing universe parser already uses (Table 3.1.3). These tables are also
present:

| Table | Metric        | Column pattern                                              |
|-------|---------------|-------------------------------------------------------------|
| 3.1.1 | vacancy_rate  | Pattern A: 5 cols/bedroom (prev, rel_prev, curr, rel_curr, yoy) |
| 3.1.2 | avg_rent      | Pattern B: 4 cols/bedroom (prev, rel_prev, curr, rel_curr)  |
| 3.1.3 | universe      | Pattern C: 2 cols/bedroom (prev, curr) — already parsed     |
| 3.1.5 | rent_change_pct | Pattern B                                                 |
| 3.1.6 | turnover_rate | Pattern A                                                   |

`median_rent` and `availability_rate` are **not present** in these Excel files
at all — they will remain NULL.

The `reliability_code` column exists inline in Pattern A/B tables (one column
after each value). We'll store the avg_rent reliability as the primary
`reliability_code` to match the existing DB column.

---

## Files to change

1. `dataflow/toronto/parsers/cmhc_excel.py`
2. `dataflow/toronto/loaders/cmhc.py`
3. `dataflow/toronto/parsers/__init__.py`
4. `dataflow/toronto/loaders/__init__.py`
5. `scripts/data/load_toronto_data.py`

---

## Step-by-step changes

### 1. `parsers/cmhc_excel.py`

**a) New dataclass `CMHCExcelRentalRecord`**

```python
@dataclass
class CMHCExcelRentalRecord:
    year: int
    zone_code: str
    zone_name: str
    bedroom_type: str
    universe: int | None = None
    avg_rent: float | None = None
    avg_rent_reliability: str | None = None
    vacancy_rate: float | None = None
    turnover_rate: float | None = None
    rent_change_pct: float | None = None
```

**b) New private helper `_find_header_row(df) -> int | None`**

Extract the header-row-finding logic already duplicated in `_parse_universe_table`
into a shared helper (avoids duplication between the new and existing parsers).

**c) New private method `_parse_metric_table(df) -> dict[str, dict]`**

Works for both Pattern A (5 cols/bedroom) and Pattern B (4 cols/bedroom).
The column offsets for both patterns are identical from the bedroom type label
position:
- `col_idx + 2` → current year value
- `col_idx + 3` → current year reliability code

Returns: `{zone_code: {"zone_name": str, bedroom_type: (value, rel_code)}}`

Handles `**` suppressed values → None.
Skips aggregate/total zone rows (same logic as existing parser).

**d) New public method `get_rental_data() -> list[CMHCExcelRentalRecord]`**

Opens the Excel file once, then for each target table:
- Finds the sheet by table number string (e.g. `"3.1.1"` in sheet name)
- Reads with `header=None`
- Calls `_parse_metric_table(df)`

Also calls existing `get_universe_data()` for universe values.

Merges all results by `(zone_code, bedroom_type)` into
`CMHCExcelRentalRecord` objects. Skips records where all metrics are None.

**e) New module-level function `parse_cmhc_excel_rental_directory()`**

Same signature as existing `parse_cmhc_excel_directory()` but calls
`get_rental_data()` and returns `dict[int, list[CMHCExcelRentalRecord]]`.

Existing `parse_cmhc_excel_directory()` and `CMHCUniverseRecord` are
**kept unchanged** for backward compatibility.

---

### 2. `loaders/cmhc.py`

**New function `load_excel_rental_data(excel_data, session=None) -> int`**

- Takes `dict[int, list[CMHCExcelRentalRecord]]`
- For each year/record: resolves `date_key` (October 1st of that year) and
  `zone_key` via zone_map (same pattern as existing `update_universe_from_excel`)
- Creates `FactRentals` with all available fields populated in a single object:
  ```python
  FactRentals(
      date_key=date_key,
      zone_key=zone_key,
      bedroom_type=record.bedroom_type,
      universe=record.universe,
      avg_rent=record.avg_rent,
      median_rent=None,           # not in Excel
      vacancy_rate=record.vacancy_rate,
      availability_rate=None,     # not in Excel
      turnover_rate=record.turnover_rate,
      rent_change_pct=record.rent_change_pct,
      reliability_code=record.avg_rent_reliability,
  )
  ```
- Uses `upsert_by_key(..., ["date_key", "zone_key", "bedroom_type"])`
- Returns total count

Because all non-NULL columns are written in one pass, the
`upsert_by_key` overwrite behaviour is safe here.

Existing `update_universe_from_excel()` is **kept unchanged**.

---

### 3. `parsers/__init__.py`

Add exports:
- `CMHCExcelRentalRecord`
- `parse_cmhc_excel_rental_directory`

---

### 4. `loaders/__init__.py`

Add exports:
- `load_excel_rental_data`

---

### 5. `scripts/data/load_toronto_data.py`

In `_load_rentals()`, replace the Excel block:

```python
# BEFORE
excel_data = parse_cmhc_excel_directory(cmhc_excel_dir, start_year=2021)
if excel_data:
    updated_count = update_universe_from_excel(excel_data, session)

# AFTER
excel_data = parse_cmhc_excel_rental_directory(cmhc_excel_dir, start_year=2021)
if excel_data:
    updated_count = load_excel_rental_data(excel_data, session)
```

Update imports accordingly.

---

## Result after implementation

| Column                    | Before | After  | Source          |
|---------------------------|--------|--------|-----------------|
| `rental_universe`         | ✅ Zone | ✅ Zone | Excel 3.1.3     |
| `avg_rent`                | ✅ CMA only | ✅ Zone | Excel 3.1.2 |
| `vacancy_rate`            | ✅ CMA only | ✅ Zone | Excel 3.1.1 |
| `turnover_rate`           | ❌ NULL | ✅ Zone | Excel 3.1.6    |
| `year_over_year_rent_change` | ❌ NULL | ✅ Zone | Excel 3.1.5 |
| `reliability_code`        | ❌ NULL | ✅ Zone | Excel 3.1.2 (avg_rent rel.) |
| `vacant_units_estimate`   | ✅ CMA only | ✅ Zone | Derived (universe × vacancy) |

Note: `median_rent` and `availability_rate` were removed from the schema entirely —
they are not available in any CMHC data source currently integrated (RMR Excel or StatCan API).
