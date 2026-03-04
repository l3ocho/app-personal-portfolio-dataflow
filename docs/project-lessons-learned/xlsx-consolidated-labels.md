# Lesson: XLSX Consolidated Age-Band Labels Match Wrong Rows

**Discovered**: Sprint 16 (March 2026)
**File affected**: `dataflow/toronto/parsers/toronto_open_data.py`
**Fields affected**: `pop_0_to_14`, `pop_65_plus`

---

## Problem

The Statistics Canada 2021 Neighbourhood Profile XLSX contains consolidated "summary"
rows for age bands (e.g., `"0 to 14 years"`, `"65 years and over"`). These consolidated
labels appear **multiple times** in the file — once in the 25% sample age distribution
section, and again in other contexts (income tables, family tables, etc.).

The `char_to_row` lookup in `_parse_census_extended()` builds a dict keyed by normalized
label and **overwrites on collision**, so only the last occurrence is retained. The last
occurrence of these consolidated labels was NOT from the age distribution section.

**Symptom**: `pop_0_to_14` values of 4–24 across all 158 neighbourhoods (correct range:
~1,500–6,000). `pop_65_plus` values of ~200 (correct range: ~500–7,000).

## Root Cause

The parser mapping used single consolidated labels:
```python
"pop_0_to_14": "0 to 14 years",       # ❌ matches wrong row
"pop_65_plus": "65 years and over",   # ❌ matches wrong row
```

## Fix

Use the individual 5-year band rows (same approach already used by `pop_15_to_24`):
```python
"pop_0_to_14": ["0 to 4 years", "5 to 9 years", "10 to 14 years"],
"pop_65_plus": [
    "65 to 69 years",
    "70 to 74 years",
    "75 to 79 years",
    "80 to 84 years",
    "85 years and over",
],
```

## Rule

**Never use a consolidated age-band label** (`"X to Y years"` spanning >5 years,
`"X years and over"`) in `CENSUS_EXTENDED_MAPPING`. These are section-header/summary
rows in the XLSX that appear in multiple contexts. Always sum the individual 5-year
interval rows instead.

**Verify**: After any new XLSX mapping, check that population age bands sum to
approximately the total population (allow ≤1% rounding difference from Statistics Canada
random rounding rules).
