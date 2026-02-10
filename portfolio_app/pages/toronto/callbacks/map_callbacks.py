"""Map callbacks for choropleth interactions."""

# mypy: disable-error-code="misc,no-untyped-def,arg-type,no-any-return"

import json
import logging

import plotly.graph_objects as go
from dash import Input, Output, State, callback, no_update

from portfolio_app.design import (
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from portfolio_app.figures.toronto import (
    create_choropleth_figure,
    create_ranking_bar,
)
from portfolio_app.toronto.services import (
    get_amenities_data,
    get_demographics_data,
    get_housing_data,
    get_neighbourhoods_geojson,
    get_overview_data,
    get_safety_data,
)

logger = logging.getLogger(__name__)


@callback(
    Output("overview-choropleth", "figure"),
    Input("overview-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_overview_choropleth(metric: str, year: str) -> go.Figure:
    """Update the overview tab choropleth map."""
    year_int = int(year) if year else 2021
    df = get_overview_data(year_int)
    geojson = get_neighbourhoods_geojson(year_int)

    if df.empty:
        return _empty_map("No data available")

    data = df.to_dict("records")

    # Color scales based on metric
    color_scale = {
        "livability_score": "Viridis",
        "safety_score": "Greens",
        "affordability_score": "Blues",
        "amenity_score": "Purples",
    }.get(metric, "Viridis")

    return create_choropleth_figure(
        geojson=geojson,
        data=data,
        location_key="neighbourhood_id",
        color_column=metric or "livability_score",
        hover_data=["neighbourhood_name", "population"],
        color_scale=color_scale,
    )


@callback(
    Output("housing-choropleth", "figure"),
    Input("housing-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_housing_choropleth(metric: str, year: str) -> go.Figure:
    """Update the housing tab choropleth map."""
    year_int = int(year) if year else 2021
    df = get_housing_data(year_int)
    geojson = get_neighbourhoods_geojson(year_int)

    if df.empty:
        return _empty_map("No housing data available")

    data = df.to_dict("records")

    color_scale = {
        "affordability_index": "RdYlGn_r",
        "avg_rent_2bed": "Oranges",
        "rent_to_income_pct": "Reds",
        "vacancy_rate": "Blues",
    }.get(metric, "Oranges")

    return create_choropleth_figure(
        geojson=geojson,
        data=data,
        location_key="neighbourhood_id",
        color_column=metric or "affordability_index",
        hover_data=["neighbourhood_name", "avg_rent_2bed", "vacancy_rate"],
        color_scale=color_scale,
    )


@callback(
    Output("safety-choropleth", "figure"),
    Input("safety-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_safety_choropleth(metric: str, year: str) -> go.Figure:
    """Update the safety tab choropleth map."""
    year_int = int(year) if year else 2021
    df = get_safety_data(year_int)
    geojson = get_neighbourhoods_geojson(year_int)

    if df.empty:
        return _empty_map("No safety data available")

    data = df.to_dict("records")

    return create_choropleth_figure(
        geojson=geojson,
        data=data,
        location_key="neighbourhood_id",
        color_column=metric or "total_crime_rate",
        hover_data=["neighbourhood_name", "total_crimes"],
        color_scale="Reds",
    )


@callback(
    Output("demographics-choropleth", "figure"),
    Input("demographics-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_demographics_choropleth(metric: str, year: str) -> go.Figure:
    """Update the demographics tab choropleth map."""
    year_int = int(year) if year else 2021
    df = get_demographics_data(year_int)
    geojson = get_neighbourhoods_geojson(year_int)

    if df.empty:
        return _empty_map("No demographics data available")

    data = df.to_dict("records")

    color_scale = {
        "population": "YlOrBr",
        "median_income": "Greens",
        "median_age": "Blues",
        "diversity_index": "Purples",
    }.get(metric, "YlOrBr")

    # Map frontend metric names to column names
    column_map = {
        "population": "population",
        "median_income": "median_household_income",
        "median_age": "median_age",
        "diversity_index": "diversity_index",
    }
    column = column_map.get(metric, "population")

    return create_choropleth_figure(
        geojson=geojson,
        data=data,
        location_key="neighbourhood_id",
        color_column=column,
        hover_data=["neighbourhood_name"],
        color_scale=color_scale,
    )


@callback(
    Output("amenities-choropleth", "figure"),
    Input("amenities-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_amenities_choropleth(metric: str, year: str) -> go.Figure:
    """Update the amenities tab choropleth map.

    Note: Amenities data uses the latest available year (2024),
    regardless of the year selector.
    """
    df = get_amenities_data()  # Always gets latest year

    if df.empty:
        return _empty_map("No amenities data available")

    # Get the year from the data itself
    amenities_year = int(df["year"].iloc[0]) if not df.empty else 2024
    geojson = get_neighbourhoods_geojson(amenities_year)
    data = df.to_dict("records")

    # Map frontend metric names to column names
    column_map = {
        "amenity_score": "amenity_score",
        "parks_per_capita": "parks_per_1000",
        "schools_per_capita": "schools_per_1000",
        "transit_score": "total_amenities_per_1000",
    }
    column = column_map.get(metric, "amenity_score")

    return create_choropleth_figure(
        geojson=geojson,
        data=data,
        location_key="neighbourhood_id",
        color_column=column,
        hover_data=["neighbourhood_name", "park_count", "school_count"],
        color_scale="Greens",
    )


@callback(
    Output("toronto-selected-neighbourhood", "data"),
    Input("overview-choropleth", "clickData"),
    Input("housing-choropleth", "clickData"),
    Input("safety-choropleth", "clickData"),
    Input("demographics-choropleth", "clickData"),
    Input("amenities-choropleth", "clickData"),
    State("toronto-tabs", "value"),
    prevent_initial_call=True,
)
def handle_map_click(
    overview_click,
    housing_click,
    safety_click,
    demographics_click,
    amenities_click,
    active_tab: str,
) -> int | None:
    """Extract neighbourhood ID from map click."""
    # Get the click data for the active tab
    click_map = {
        "overview": overview_click,
        "housing": housing_click,
        "safety": safety_click,
        "demographics": demographics_click,
        "amenities": amenities_click,
    }

    click_data = click_map.get(active_tab)
    print(f"🖱️ CLICK on tab '{active_tab}'")
    logger.debug(f"Click detected on tab: {active_tab}, data: {click_data}")

    if not click_data or "points" not in click_data or len(click_data["points"]) == 0:
        return no_update

    try:
        point = click_data["points"][0]
        logger.debug(f"Point keys: {point.keys()}")
        logger.debug(f"Full point: {json.dumps(point, default=str)}")

        # Try to extract neighbourhood_id from multiple possible locations
        # For px.choropleth_mapbox, it should be in 'location'
        location = None
        if "location" in point:
            location = point["location"]
            logger.debug(f"Found location in 'location' field: {location}")
        elif "customdata" in point and point["customdata"]:
            location = point["customdata"][0]
            logger.debug(f"Found location in customdata: {location}")
        elif "properties" in point and isinstance(point["properties"], dict):
            location = point["properties"].get("neighbourhood_id")
            logger.debug(f"Found location in properties: {location}")

        if location is not None:
            neighbourhood_id = int(location)
            print(
                f"✅ EXTRACTED neighbourhood_id={neighbourhood_id} "
                f"from location={location}"
            )
            logger.debug(f"Returning neighbourhood_id: {neighbourhood_id}")
            return neighbourhood_id
        else:
            print(f"❌ Could not extract location from point: {point}")
            logger.warning(f"Could not extract location from point: {point}")
    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"❌ ERROR extracting location: {e}")
        logger.error(f"Error extracting location: {e}", exc_info=True)

    print("❌ Returning no_update from handle_map_click")
    logger.warning("Returning no_update from handle_map_click")
    return no_update


@callback(
    Output("overview-rankings-chart", "figure"),
    Input("overview-metric-select", "value"),
    Input("toronto-year-select", "value"),
)
def update_rankings_chart(metric: str, year: str) -> go.Figure:
    """Update the top/bottom rankings bar chart."""
    year_int = int(year) if year else 2021
    df = get_overview_data(year_int)

    if df.empty:
        return _empty_chart("No data available")

    # Use the selected metric for ranking
    metric = metric or "livability_score"
    data = df.to_dict("records")

    return create_ranking_bar(
        data=data,
        name_column="neighbourhood_name",
        value_column=metric,
        title=f"Top & Bottom 10 by {metric.replace('_', ' ').title()}",
        top_n=10,
        bottom_n=10,
    )


def _empty_map(message: str) -> go.Figure:
    """Create an empty map with a message."""
    fig = go.Figure()
    fig.update_layout(
        mapbox={
            "style": "carto-darkmatter",
            "center": {"lat": 43.7, "lon": -79.4},
            "zoom": 9.5,
        },
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=PAPER_BG,
        font_color=TEXT_PRIMARY,
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
