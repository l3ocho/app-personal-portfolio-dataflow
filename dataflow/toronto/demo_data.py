"""Demo/sample data for testing the Toronto Housing Dashboard without full pipeline.

This module provides synthetic data for development and demonstration purposes.
Replace with real data from the database in production.
"""

from datetime import date
from typing import Any


def get_demo_rental_data() -> list[dict[str, Any]]:
    """Return sample rental data for visualization."""
    data = []

    zones = [
        ("Zone01", "Downtown"),
        ("Zone02", "Midtown"),
        ("Zone03", "North York"),
        ("Zone04", "Scarborough"),
        ("Zone05", "Etobicoke"),
    ]

    bedroom_types = ["bachelor", "1_bedroom", "2_bedroom", "3_bedroom"]

    base_rents = {
        "bachelor": 1800,
        "1_bedroom": 2200,
        "2_bedroom": 2800,
        "3_bedroom": 3400,
    }

    for year in [2021, 2022, 2023, 2024, 2025]:
        for zone_code, zone_name in zones:
            for bedroom in bedroom_types:
                # Rental trend: ~5% increase per year
                year_factor = 1 + ((year - 2021) * 0.05)
                base_rent = base_rents[bedroom]

                data.append(
                    {
                        "zone_code": zone_code,
                        "zone_name": zone_name,
                        "survey_year": year,
                        "full_date": date(year, 10, 1),
                        "bedroom_type": bedroom,
                        "average_rent": int(base_rent * year_factor),
                        "vacancy_rate": round(
                            2.5 - (year - 2021) * 0.3, 1
                        ),  # Decreasing vacancy
                        "universe": 5000 + (year - 2021) * 200,
                    }
                )

    return data


def get_demo_policy_events() -> list[dict[str, Any]]:
    """Return sample policy events for annotation."""
    return [
        {
            "event_date": date(2024, 6, 5),
            "effective_date": date(2024, 6, 5),
            "level": "federal",
            "category": "monetary",
            "title": "BoC Rate Cut (25bp)",
            "description": "Bank of Canada cuts overnight rate by 25 basis points to 4.75%",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 7, 24),
            "effective_date": date(2024, 7, 24),
            "level": "federal",
            "category": "monetary",
            "title": "BoC Rate Cut (25bp)",
            "description": "Bank of Canada cuts overnight rate by 25 basis points to 4.50%",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 9, 4),
            "effective_date": date(2024, 9, 4),
            "level": "federal",
            "category": "monetary",
            "title": "BoC Rate Cut (25bp)",
            "description": "Bank of Canada cuts overnight rate by 25 basis points to 4.25%",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 10, 23),
            "effective_date": date(2024, 10, 23),
            "level": "federal",
            "category": "monetary",
            "title": "BoC Rate Cut (50bp)",
            "description": "Bank of Canada cuts overnight rate by 50 basis points to 3.75%",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 12, 11),
            "effective_date": date(2024, 12, 11),
            "level": "federal",
            "category": "monetary",
            "title": "BoC Rate Cut (50bp)",
            "description": "Bank of Canada cuts overnight rate by 50 basis points to 3.25%",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 9, 16),
            "effective_date": date(2024, 12, 15),
            "level": "federal",
            "category": "regulatory",
            "title": "CMHC 30-Year Amortization",
            "description": "30-year amortization extended to all first-time buyers and new builds",
            "expected_direction": "bullish",
        },
        {
            "event_date": date(2024, 9, 16),
            "effective_date": date(2024, 12, 15),
            "level": "federal",
            "category": "regulatory",
            "title": "Insured Mortgage Cap $1.5M",
            "description": "Insured mortgage cap raised from $1M to $1.5M",
            "expected_direction": "bullish",
        },
    ]


def get_demo_summary_metrics() -> dict[str, dict[str, Any]]:
    """Return summary metrics for KPI cards."""
    return {
        "avg_rent": {
            "value": 2450,
            "title": "Avg. Rent (2025)",
            "delta": 3.2,
            "delta_suffix": "%",
            "prefix": "$",
            "format_spec": ",.0f",
            "positive_is_good": False,
        },
        "vacancy_rate": {
            "value": 1.8,
            "title": "Vacancy Rate",
            "delta": -0.4,
            "delta_suffix": "pp",
            "suffix": "%",
            "format_spec": ".1f",
            "positive_is_good": False,
        },
    }
