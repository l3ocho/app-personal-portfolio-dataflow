"""Chart callbacks for supporting visualizations."""
# mypy: disable-error-code="misc,no-untyped-def,arg-type"

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback

from portfolio_app.design import (
    CHART_PALETTE,
    GRID_COLOR,
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from portfolio_app.figures.toronto import (
    create_donut_chart,
    create_horizontal_bar,
    create_radar_figure,
    create_scatter_figure,
)
from portfolio_app.toronto.services import (
    get_amenities_data,
    get_city_averages,
    get_demographics_data,
    get_housing_data,
    get_neighbourhood_details,
    get_safety_data,
)


@callback(
    Output("overview-scatter-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_overview_scatter(year: str) -> go.Figure:
    """Update income vs safety scatter plot."""
    year_int = int(year) if year else 2021
    df = get_demographics_data(year_int)
    safety_df = get_safety_data(year_int)

    if df.empty or safety_df.empty:
        return _empty_chart("No data available")

    # Merge demographics with safety
    merged = df.merge(
        safety_df[["neighbourhood_id", "total_crime_rate"]],
        on="neighbourhood_id",
        how="left",
    )

    # Compute safety score (inverse of crime rate)
    if "total_crime_rate" in merged.columns:
        max_crime = merged["total_crime_rate"].max()
        if max_crime and max_crime > 0:
            merged["safety_score"] = 100 - (
                merged["total_crime_rate"] / max_crime * 100
            )
        else:
            merged["safety_score"] = 50  # Default if no crime data

    # Fill NULL population with median or default value for sizing
    if "population" in merged.columns:
        median_pop = merged["population"].median()
        default_pop = median_pop if pd.notna(median_pop) else 10000
        merged["population"] = merged["population"].fillna(default_pop)

    # Filter rows with required data for scatter plot
    merged = merged.dropna(subset=["median_household_income", "safety_score"])

    if merged.empty:
        return _empty_chart("Insufficient data for scatter plot")

    data = merged.to_dict("records")

    return create_scatter_figure(
        data=data,
        x_column="median_household_income",
        y_column="safety_score",
        name_column="neighbourhood_name",
        size_column="population",
        title="Income vs Safety",
        x_title="Median Household Income ($)",
        y_title="Safety Score",
        trendline=True,
    )


@callback(
    Output("housing-trend-chart", "figure"),
    Input("toronto-year-select", "value"),
    Input("toronto-selected-neighbourhood", "data"),
)
def update_housing_trend(year: str, neighbourhood_id: int | None) -> go.Figure:
    """Update housing rent trend chart."""
    # For now, show city averages as we don't have multi-year data
    # This would be a time series if we had historical data
    year_int = int(year) if year else 2021
    averages = get_city_averages(year_int)

    if not averages:
        return _empty_chart("No trend data available")

    # Placeholder for trend data - would be historical
    base_rent = averages.get("avg_rent_2bed") or 2000
    data = [
        {"year": "2019", "avg_rent": base_rent * 0.85},
        {"year": "2020", "avg_rent": base_rent * 0.88},
        {"year": "2021", "avg_rent": base_rent * 0.92},
        {"year": "2022", "avg_rent": base_rent * 0.96},
        {"year": "2023", "avg_rent": base_rent},
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[d["year"] for d in data],
            y=[d["avg_rent"] for d in data],
            mode="lines+markers",
            line={"color": CHART_PALETTE[0], "width": 2},
            marker={"size": 8},
            name="City Average",
        )
    )

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR},
        yaxis={"gridcolor": GRID_COLOR, "title": "Avg Rent (2BR)"},
        showlegend=False,
        margin={"l": 40, "r": 10, "t": 10, "b": 30},
    )

    return fig


@callback(
    Output("housing-types-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_housing_types(year: str) -> go.Figure:
    """Update dwelling types breakdown chart."""
    year_int = int(year) if year else 2021
    df = get_housing_data(year_int)

    if df.empty:
        return _empty_chart("No data available")

    # Aggregate tenure types across city
    owner_pct = df["pct_owner_occupied"].mean()
    renter_pct = df["pct_renter_occupied"].mean()

    data = [
        {"type": "Owner Occupied", "percentage": owner_pct},
        {"type": "Renter Occupied", "percentage": renter_pct},
    ]

    return create_donut_chart(
        data=data,
        name_column="type",
        value_column="percentage",
        colors=[CHART_PALETTE[3], CHART_PALETTE[0]],  # Teal for owner, blue for renter
    )


@callback(
    Output("safety-trend-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_safety_trend(year: str) -> go.Figure:
    """Update crime trend chart."""
    # Placeholder for trend - would need historical data
    data = [
        {"year": "2019", "crime_rate": 4500},
        {"year": "2020", "crime_rate": 4200},
        {"year": "2021", "crime_rate": 4100},
        {"year": "2022", "crime_rate": 4300},
        {"year": "2023", "crime_rate": 4250},
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[d["year"] for d in data],
            y=[d["crime_rate"] for d in data],
            mode="lines+markers",
            line={"color": CHART_PALETTE[5], "width": 2},  # Vermillion
            marker={"size": 8},
            fill="tozeroy",
            fillcolor="rgba(213, 94, 0, 0.1)",  # Vermillion with opacity
        )
    )

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR},
        yaxis={"gridcolor": GRID_COLOR, "title": "Crime Rate per 100K"},
        showlegend=False,
        margin={"l": 40, "r": 10, "t": 10, "b": 30},
    )

    return fig


@callback(
    Output("safety-types-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_safety_types(year: str) -> go.Figure:
    """Update crime by category chart."""
    year_int = int(year) if year else 2021
    df = get_safety_data(year_int)

    if df.empty:
        return _empty_chart("No data available")

    # Aggregate crime types across city
    violent = df["violent_crimes"].sum() if "violent_crimes" in df.columns else 0
    property_crimes_col = (
        df["property_crimes"].sum() if "property_crimes" in df.columns else 0
    )
    theft = df["theft_crimes"].sum() if "theft_crimes" in df.columns else 0
    total_crimes = df["total_crimes"].sum() if "total_crimes" in df.columns else 0
    other = max(0, total_crimes - violent - property_crimes_col - theft)

    data = [
        {"category": "Violent", "count": int(violent)},
        {"category": "Property", "count": int(property_crimes_col)},
        {"category": "Theft", "count": int(theft)},
        {"category": "Other", "count": int(other)},
    ]

    return create_horizontal_bar(
        data=data,
        name_column="category",
        value_column="count",
        color=CHART_PALETTE[5],  # Vermillion for crime
    )


@callback(
    Output("demographics-age-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_demographics_age(year: str) -> go.Figure:
    """Update age distribution chart."""
    year_int = int(year) if year else 2021
    df = get_demographics_data(year_int)

    if df.empty:
        return _empty_chart("No data available")

    # Calculate average age distribution
    under_18 = df["pct_under_18"].mean() if "pct_under_18" in df.columns else 20
    age_18_64 = df["pct_18_to_64"].mean() if "pct_18_to_64" in df.columns else 65
    over_65 = df["pct_65_plus"].mean() if "pct_65_plus" in df.columns else 15

    data = [
        {"age_group": "Under 18", "percentage": under_18},
        {"age_group": "18-64", "percentage": age_18_64},
        {"age_group": "65+", "percentage": over_65},
    ]

    return create_donut_chart(
        data=data,
        name_column="age_group",
        value_column="percentage",
        colors=[
            CHART_PALETTE[2],
            CHART_PALETTE[0],
            CHART_PALETTE[4],
        ],  # Sky, Blue, Yellow
    )


@callback(
    Output("demographics-income-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_demographics_income(year: str) -> go.Figure:
    """Update income distribution chart."""
    year_int = int(year) if year else 2021
    df = get_demographics_data(year_int)

    if df.empty:
        return _empty_chart("No data available")

    # Create income quintile distribution
    if "income_quintile" in df.columns:
        quintile_counts = df["income_quintile"].value_counts().sort_index()
        data = [
            {"bracket": f"Q{q}", "count": int(count)}
            for q, count in quintile_counts.items()
        ]
    else:
        # Fallback to placeholder
        data = [
            {"bracket": "Q1 (Low)", "count": 32},
            {"bracket": "Q2", "count": 32},
            {"bracket": "Q3 (Mid)", "count": 32},
            {"bracket": "Q4", "count": 31},
            {"bracket": "Q5 (High)", "count": 31},
        ]

    return create_horizontal_bar(
        data=data,
        name_column="bracket",
        value_column="count",
        color=CHART_PALETTE[3],  # Teal
        sort=False,
    )


@callback(
    Output("amenities-breakdown-chart", "figure"),
    Input("toronto-year-select", "value"),
)
def update_amenities_breakdown(year: str) -> go.Figure:
    """Update amenity breakdown chart.

    Uses latest available amenities year (2024).
    """
    df = get_amenities_data()  # Always gets latest year

    if df.empty:
        return _empty_chart("No data available")

    # Aggregate amenity counts (handling both possible column names)
    parks_col = "parks_count" if "parks_count" in df.columns else "park_count"
    schools_col = "schools_count" if "schools_count" in df.columns else "school_count"
    parks = df[parks_col].sum() if parks_col in df.columns else 0
    schools = df[schools_col].sum() if schools_col in df.columns else 0
    childcare = df["childcare_count"].sum() if "childcare_count" in df.columns else 0

    data = [
        {"type": "Parks", "count": int(parks)},
        {"type": "Schools", "count": int(schools)},
        {"type": "Childcare", "count": int(childcare)},
    ]

    return create_horizontal_bar(
        data=data,
        name_column="type",
        value_column="count",
        color=CHART_PALETTE[3],  # Teal
    )


@callback(
    Output("amenities-radar-chart", "figure"),
    Input("toronto-year-select", "value"),
    Input("toronto-selected-neighbourhood", "data"),
)
def update_amenities_radar(year: str, neighbourhood_id: int | None) -> go.Figure:
    """Update amenity comparison radar chart.

    Uses latest available amenities year (2024).
    """
    # Get latest amenities data year
    amenities_df = get_amenities_data()
    amenities_year = (
        int(amenities_df["year"].iloc[0]) if not amenities_df.empty else 2024
    )

    # City averages come from overview table (2021 data)
    # Amenities data is always latest year (2024)
    averages = get_city_averages(2021)

    amenity_score = averages.get("avg_amenity_score") or 50
    city_data = {
        "parks_per_1000": amenity_score / 100 * 10,
        "schools_per_1000": amenity_score / 100 * 5,
        "childcare_per_1000": amenity_score / 100 * 3,
        "transit_access": 70,
    }

    data = [city_data]

    # Add selected neighbourhood if available
    if neighbourhood_id:
        details = get_neighbourhood_details(neighbourhood_id, amenities_year)
        if details:
            park_cnt = details.get("park_count") or details.get("parks_count") or 0
            school_cnt = (
                details.get("school_count") or details.get("schools_count") or 0
            )
            selected_data = {
                "parks_per_1000": park_cnt / 10,
                "schools_per_1000": school_cnt / 5,
                "childcare_per_1000": 3,
                "transit_access": 70,
            }
            data.insert(0, selected_data)

    return create_radar_figure(
        data=data,
        metrics=[
            "parks_per_1000",
            "schools_per_1000",
            "childcare_per_1000",
            "transit_access",
        ],
        fill=True,
    )


def _empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message."""
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": TEXT_SECONDARY},
    )
    return fig
