"""Selection callbacks for dropdowns and neighbourhood details."""
# mypy: disable-error-code="misc,no-untyped-def,type-arg"

import dash_mantine_components as dmc
from dash import Input, Output, callback

from portfolio_app.toronto.services import (
    get_amenities_data,
    get_city_averages,
    get_neighbourhood_details,
    get_neighbourhood_list,
)


@callback(
    Output("toronto-neighbourhood-select", "data"),
    Input("toronto-year-select", "value"),
)
def populate_neighbourhood_dropdown(year: str) -> list[dict]:
    """Populate the neighbourhood search dropdown."""
    year_int = int(year) if year else 2021
    neighbourhoods = get_neighbourhood_list(year_int)

    return [
        {"value": str(n["neighbourhood_id"]), "label": n["neighbourhood_name"]}
        for n in neighbourhoods
    ]


@callback(
    Output("toronto-selected-neighbourhood", "data", allow_duplicate=True),
    Input("toronto-neighbourhood-select", "value"),
    prevent_initial_call=True,
)
def select_from_dropdown(value: str | None) -> int | None:
    """Update selected neighbourhood from dropdown."""
    if value:
        return int(value)
    return None


@callback(
    Output("toronto-compare-btn", "disabled"),
    Input("toronto-selected-neighbourhood", "data"),
)
def toggle_compare_button(neighbourhood_id: int | None) -> bool:
    """Enable compare button when a neighbourhood is selected."""
    return neighbourhood_id is None


# Overview tab KPIs
@callback(
    Output("overview-city-avg", "children"),
    Input("toronto-year-select", "value"),
)
def update_overview_city_avg(year: str) -> str:
    """Update the city average livability score."""
    year_int = int(year) if year else 2021
    averages = get_city_averages(year_int)
    score = averages.get("avg_livability_score", 72)
    return f"{score:.0f}" if score else "—"


@callback(
    Output("overview-selected-name", "children"),
    Output("overview-selected-scores", "children"),
    Input("toronto-selected-neighbourhood", "data"),
    Input("toronto-year-select", "value"),
)
def update_overview_selected(neighbourhood_id: int | None, year: str):
    """Update the selected neighbourhood details in overview tab."""
    if not neighbourhood_id:
        return "Click map to select", [dmc.Text("—", c="dimmed")]

    year_int = int(year) if year else 2021
    details = get_neighbourhood_details(neighbourhood_id, year_int)

    if not details:
        return "Unknown", [dmc.Text("No data", c="dimmed")]

    name = details.get("neighbourhood_name", "Unknown")
    scores = [
        dmc.Group(
            [
                dmc.Text("Livability:", size="sm"),
                dmc.Text(
                    f"{details.get('livability_score', 0):.0f}", size="sm", fw=700
                ),
            ],
            justify="space-between",
        ),
        dmc.Group(
            [
                dmc.Text("Safety:", size="sm"),
                dmc.Text(f"{details.get('safety_score', 0):.0f}", size="sm", fw=700),
            ],
            justify="space-between",
        ),
        dmc.Group(
            [
                dmc.Text("Affordability:", size="sm"),
                dmc.Text(
                    f"{details.get('affordability_score', 0):.0f}", size="sm", fw=700
                ),
            ],
            justify="space-between",
        ),
    ]

    return name, scores


# Housing tab KPIs
@callback(
    Output("housing-city-rent", "children"),
    Output("housing-rent-change", "children"),
    Input("toronto-year-select", "value"),
)
def update_housing_kpis(year: str):
    """Update housing tab KPI cards."""
    year_int = int(year) if year else 2021
    averages = get_city_averages(year_int)

    rent = averages.get("avg_rent_2bed", 2450)
    rent_str = f"${rent:,.0f}" if rent else "—"

    # Placeholder change - would come from historical data
    change = "+4.2% YoY"

    return rent_str, change


@callback(
    Output("housing-selected-name", "children"),
    Output("housing-selected-details", "children"),
    Input("toronto-selected-neighbourhood", "data"),
    Input("toronto-year-select", "value"),
)
def update_housing_selected(neighbourhood_id: int | None, year: str):
    """Update selected neighbourhood details in housing tab."""
    if not neighbourhood_id:
        return "Click map to select", [dmc.Text("—", c="dimmed")]

    year_int = int(year) if year else 2021
    details = get_neighbourhood_details(neighbourhood_id, year_int)

    if not details:
        return "Unknown", [dmc.Text("No data", c="dimmed")]

    name = details.get("neighbourhood_name", "Unknown")
    rent = details.get("avg_rent_2bed")
    vacancy = details.get("vacancy_rate")

    info = [
        dmc.Text(f"2BR Rent: ${rent:,.0f}" if rent else "2BR Rent: —", size="sm"),
        dmc.Text(f"Vacancy: {vacancy:.1f}%" if vacancy else "Vacancy: —", size="sm"),
    ]

    return name, info


# Safety tab KPIs
@callback(
    Output("safety-city-rate", "children"),
    Output("safety-rate-change", "children"),
    Input("toronto-year-select", "value"),
)
def update_safety_kpis(year: str):
    """Update safety tab KPI cards."""
    year_int = int(year) if year else 2021
    averages = get_city_averages(year_int)

    rate = averages.get("avg_crime_rate", 4250)
    rate_str = f"{rate:,.0f}" if rate else "—"

    # Placeholder change
    change = "-2.1% YoY"

    return rate_str, change


@callback(
    Output("safety-selected-name", "children"),
    Output("safety-selected-details", "children"),
    Input("toronto-selected-neighbourhood", "data"),
    Input("toronto-year-select", "value"),
)
def update_safety_selected(neighbourhood_id: int | None, year: str):
    """Update selected neighbourhood details in safety tab."""
    if not neighbourhood_id:
        return "Click map to select", [dmc.Text("—", c="dimmed")]

    year_int = int(year) if year else 2021
    details = get_neighbourhood_details(neighbourhood_id, year_int)

    if not details:
        return "Unknown", [dmc.Text("No data", c="dimmed")]

    name = details.get("neighbourhood_name", "Unknown")
    crime_rate = details.get("crime_rate_per_100k")

    info = [
        dmc.Text(
            f"Crime Rate: {crime_rate:,.0f}/100K" if crime_rate else "Crime Rate: —",
            size="sm",
        ),
    ]

    return name, info


# Demographics tab KPIs
@callback(
    Output("demographics-city-pop", "children"),
    Output("demographics-pop-change", "children"),
    Input("toronto-year-select", "value"),
)
def update_demographics_kpis(year: str):
    """Update demographics tab KPI cards."""
    year_int = int(year) if year else 2021
    averages = get_city_averages(year_int)

    pop = averages.get("total_population", 2790000)
    if pop and pop >= 1000000:
        pop_str = f"{pop / 1000000:.2f}M"
    elif pop:
        pop_str = f"{pop:,.0f}"
    else:
        pop_str = "—"

    change = "+2.3% since 2016"

    return pop_str, change


@callback(
    Output("demographics-selected-name", "children"),
    Output("demographics-selected-details", "children"),
    Input("toronto-selected-neighbourhood", "data"),
    Input("toronto-year-select", "value"),
)
def update_demographics_selected(neighbourhood_id: int | None, year: str):
    """Update selected neighbourhood details in demographics tab."""
    if not neighbourhood_id:
        return "Click map to select", [dmc.Text("—", c="dimmed")]

    year_int = int(year) if year else 2021
    details = get_neighbourhood_details(neighbourhood_id, year_int)

    if not details:
        return "Unknown", [dmc.Text("No data", c="dimmed")]

    name = details.get("neighbourhood_name", "Unknown")
    pop = details.get("population")
    income = details.get("median_household_income")

    info = [
        dmc.Text(f"Population: {pop:,}" if pop else "Population: —", size="sm"),
        dmc.Text(
            f"Median Income: ${income:,.0f}" if income else "Median Income: —",
            size="sm",
        ),
    ]

    return name, info


# Amenities tab KPIs
@callback(
    Output("amenities-city-score", "children"),
    Input("toronto-year-select", "value"),
)
def update_amenities_kpis(year: str) -> str:
    """Update amenities tab KPI cards.

    Uses latest available amenities year (2024).
    """
    amenities_df = get_amenities_data()
    if amenities_df.empty:
        return "—"

    # City averages come from overview table which has 2021 data
    # Amenities data is always latest year (2024)
    averages = get_city_averages(2021)

    score = averages.get("avg_amenity_score", 68)
    return f"{score:.0f}" if score else "—"


@callback(
    Output("amenities-selected-name", "children"),
    Output("amenities-selected-details", "children"),
    Input("toronto-selected-neighbourhood", "data"),
    Input("toronto-year-select", "value"),
)
def update_amenities_selected(neighbourhood_id: int | None, year: str):
    """Update selected neighbourhood details in amenities tab.

    Uses latest available amenities year (2024).
    """
    if not neighbourhood_id:
        return "Click map to select", [dmc.Text("—", c="dimmed")]

    amenities_df = get_amenities_data()
    amenities_year = (
        int(amenities_df["year"].iloc[0]) if not amenities_df.empty else 2024
    )
    details = get_neighbourhood_details(neighbourhood_id, amenities_year)

    if not details:
        return "Unknown", [dmc.Text("No data", c="dimmed")]

    name = details.get("neighbourhood_name", "Unknown")
    parks = details.get("parks_count") or details.get("park_count")
    schools = details.get("schools_count") or details.get("school_count")

    info = [
        dmc.Text(f"Parks: {parks}" if parks is not None else "Parks: —", size="sm"),
        dmc.Text(
            f"Schools: {schools}" if schools is not None else "Schools: —", size="sm"
        ),
    ]

    return name, info
