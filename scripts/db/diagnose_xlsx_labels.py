#!/usr/bin/env python
"""Diagnostic script: dump actual XLSX characteristic strings.

Fetches the 2021 Statistics Canada neighbourhood profiles XLSX and prints
all Characteristic values so we can compare with CENSUS_EXTENDED_MAPPING.

Usage:
    .venv/bin/python scripts/db/diagnose_xlsx_labels.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataflow.toronto.parsers.toronto_open_data import TorontoOpenDataParser

MAPPING_LABELS = {
    # All labels from CENSUS_EXTENDED_MAPPING (both str specs and tuple numerator/denominator)
    "Total - Age groups of the population - 100% data",
    "Under 15 years",
    "15 to 19 years",
    "20 to 24 years",
    "25 to 29 years",
    "30 to 34 years",
    "35 to 39 years",
    "40 to 44 years",
    "45 to 49 years",
    "50 to 54 years",
    "55 to 59 years",
    "60 to 64 years",
    "65 years and over",
    "Total private dwellings",
    "Private dwellings occupied by usual residents",
    "Average household size",
    "Average after-tax income of households in 2020 ($)",
    "Owner",
    "Total - Private households by tenure - 25% sample data",
    "Renter",
    "Suitable",
    "Total - Private households by housing suitability - 25% sample data",
    "Average monthly shelter costs for owned dwellings ($)",
    "Average monthly shelter costs for rented dwellings ($)",
    "Spending 30% or more of income on shelter costs",
    "No certificate, diploma or degree",
    "Total - Highest certificate, diploma or degree for the population aged 15 years and over in private households - 25% sample data",
    "High (secondary) school diploma or equivalency certificate",
    "Postsecondary certificate or diploma below bachelor level",
    "Bachelor's degree or higher",
    "Postsecondary certificate, diploma or degree",
    "Participation rate",
    "Employment rate",
    "Unemployment rate",
    "Worked full year, full time",
    "Total - Experienced labour force aged 15 years and over by work activity in 2020 - 25% sample data",
    "Median after-tax income of households in 2020 ($)",
    "Median employment income in 2020 among recipients ($)",
    "In low income based on the Low-income cut-offs, after tax (LICO-AT)",
    "Total - Low-income status in 2020 for the population in private households to whom the low-income concept is applicable - 100% data",
    "In low income based on the Market Basket Measure (MBM)",
    "Immigrants",
    "Total - Immigrant status and period of immigration for the population in private households - 25% sample data",
    "2016 to 2021",
    "Total visible minority population",
    "Total - Visible minority for the population in private households - 25% sample data",
    "Total - Indigenous identity",
    "Total - Indigenous identity for the population in private households - 25% sample data",
    "English only",
    "Total - Knowledge of official languages for the population in private households - 25% sample data",
    "French only",
    "Neither English nor French",
    "English and French",
    "Non-movers",
    "Total - Mobility status 5 years ago - 25% sample data",
    "Movers within census subdivision (CSD)",
    "External migrants",
    "Car, truck or van - as a driver or passenger",
    "Total - Main mode of commuting for the employed labour force aged 15 years and over in private households with a usual place of work or no fixed workplace address - 25% sample data",
    "Public transit",
    "Walked",
    "Worked at home",
    "Total - Place of work status for the employed labour force aged 15 years and over in private households - 25% sample data",
    "Median age of the population",
    "Lone-parent census families",
    "Total - Census family structure including whether children are present - 25% sample data",
    "Average number of children in census families",
    "Major repairs needed",
    "Total - Occupied private dwellings by dwelling condition - 25% sample data",
    "Total - Shelter-cost-to-income ratio - 25% sample data",
    "Not suitable",
    "Median commuting duration (minutes)",
    "0 Management occupations",
    "Total - Occupation - National Occupational Classification (NOC) 2021 - for the employed labour force aged 15 years and over in private households - 25% sample data",
    "1 Business, finance and administration occupations",
    "6 Sales and service occupations",
    "7 Trades, transport and equipment operators and related occupations",
    "Population density per square kilometre",
}


def main():
    parser = TorontoOpenDataParser()

    print("Fetching XLSX...")
    raw_records = parser._fetch_xlsx_as_records(
        parser.DATASETS["neighbourhood_profiles"],
        name_filter="2021",
    )

    print(f"Total rows: {len(raw_records)}\n")

    # Build the set of actual characteristics (stripped, as used in char_to_row)
    actual_chars = set()
    for row in raw_records:
        char = str(row.get("Characteristic", "")).strip()
        if char:
            actual_chars.add(char)

    # Compare
    mapping_lower = {label.lower() for label in MAPPING_LABELS}
    actual_lower = {c.lower() for c in actual_chars}

    matched = mapping_lower & actual_lower
    unmatched = mapping_lower - actual_lower

    print("=== MATCH SUMMARY ===")
    print(f"Mapping labels:  {len(MAPPING_LABELS)}")
    print(f"Matched:         {len(matched)}")
    print(f"Unmatched:       {len(unmatched)}\n")

    print("=== UNMATCHED MAPPING LABELS ===")
    for label in sorted(unmatched):
        print(f"  MISSING: {label!r}")

    print("\n=== SEARCHING FOR SIMILAR ROWS IN XLSX ===")
    # For each unmatched label, find the closest actual characteristic
    for unmatched_label in sorted(unmatched):
        # Find similar chars using keyword hints
        unmatched_lower = unmatched_label.lower()
        # Simple: find rows containing first 10 chars of the unmatched label
        prefix = unmatched_lower[:20]
        similar = [
            c
            for c in actual_chars
            if any(word in c.lower() for word in prefix.split()[:3])
        ][:5]
        if similar:
            print(f"\n  Unmatched: {unmatched_label!r}")
            for s in similar[:5]:
                print(f"    ~~ {s!r}")

    print("\n\n=== ALL XLSX CHARACTERISTICS (first 200) ===")
    for char in sorted(actual_chars)[:200]:
        print(f"  {char!r}")

    # Also print all rows containing key words
    print("\n\n=== ROWS CONTAINING 'age groups' ===")
    for char in actual_chars:
        if "age groups" in char.lower() or "age of" in char.lower():
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'dwellings' ===")
    for char in actual_chars:
        if "dwelling" in char.lower():
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'labour force' or 'participation' ===")
    for char in actual_chars:
        if "labour force" in char.lower() or "participation rate" in char.lower():
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'low-income' or 'lico' ===")
    for char in actual_chars:
        if (
            "low-income" in char.lower()
            or "lico" in char.lower()
            or "market basket" in char.lower()
        ):
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'commut' ===")
    for char in actual_chars:
        if "commut" in char.lower():
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'occupation' ===")
    for char in actual_chars:
        if "occupation" in char.lower() or "management" in char.lower():
            print(f"  {char!r}")

    print("\n=== ROWS CONTAINING 'immigrant' ===")
    for char in actual_chars:
        if "immigrant" in char.lower():
            print(f"  {char!r}")


if __name__ == "__main__":
    main()
