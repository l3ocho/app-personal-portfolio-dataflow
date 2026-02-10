"""Choropleth map figure factory for Toronto housing data."""

from typing import Any

import plotly.express as px
import plotly.graph_objects as go

from portfolio_app.design import (
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_choropleth_figure(
    geojson: dict[str, Any] | None,
    data: list[dict[str, Any]],
    location_key: str,
    color_column: str,
    hover_data: list[str] | None = None,
    color_scale: str = "Blues",
    title: str | None = None,
    map_style: str = "carto-positron",
    center: dict[str, float] | None = None,
    zoom: float = 9.45,
) -> go.Figure:
    """Create a choropleth map figure.

    Args:
        geojson: GeoJSON FeatureCollection for boundaries.
        data: List of data records with location keys and values.
        location_key: Column name for location identifier.
        color_column: Column name for color values.
        hover_data: Additional columns to show on hover.
        color_scale: Plotly color scale name.
        title: Optional chart title.
        map_style: Mapbox style (carto-positron, open-street-map, etc.).
        center: Map center coordinates {"lat": float, "lon": float}.
        zoom: Initial zoom level.

    Returns:
        Plotly Figure object.
    """
    # Default center to Toronto
    if center is None:
        center = {"lat": 43.7, "lon": -79.4}

    # Use dark-mode friendly map style by default
    if map_style == "carto-positron":
        map_style = "carto-darkmatter"

    # If no geojson provided, create a placeholder map
    if geojson is None or not data:
        fig = go.Figure(go.Scattermapbox())
        fig.update_layout(
            mapbox={
                "style": map_style,
                "center": center,
                "zoom": zoom,
            },
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            title=title or "Toronto Housing Map",
            height=450,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            font_color=TEXT_PRIMARY,
        )
        fig.add_annotation(
            text="No geometry data available. Complete QGIS digitization to enable map.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 14, "color": TEXT_SECONDARY},
        )
        return fig

    # Create choropleth with data
    import pandas as pd

    df = pd.DataFrame(data)

    # Use dark-mode friendly map style
    effective_map_style = (
        "carto-darkmatter" if map_style == "carto-positron" else map_style
    )

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations=location_key,
        featureidkey=f"properties.{location_key}",
        color=color_column,
        color_continuous_scale=color_scale,
        hover_data=hover_data,
        mapbox_style=effective_map_style,
        center=center,
        zoom=zoom,
        opacity=0.7,
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        title=title,
        height=450,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        coloraxis_colorbar={
            "title": {"text": ""},
            "thickness": 15,
            "len": 0.7,
            "tickfont": {"color": TEXT_PRIMARY},
        },
    )

    return fig


def create_zone_map(
    zones_geojson: dict[str, Any] | None,
    rental_data: list[dict[str, Any]],
    metric: str = "avg_rent",
) -> go.Figure:
    """Create choropleth map for CMHC zones.

    Args:
        zones_geojson: GeoJSON for CMHC zone boundaries.
        rental_data: Rental statistics by zone.
        metric: Metric to display (avg_rent, vacancy_rate, etc.).

    Returns:
        Plotly Figure object.
    """
    hover_columns = ["zone_name", "avg_rent", "vacancy_rate", "rental_universe"]

    return create_choropleth_figure(
        geojson=zones_geojson,
        data=rental_data,
        location_key="zone_code",
        color_column=metric,
        hover_data=[c for c in hover_columns if c != metric],
        color_scale="Oranges" if "rent" in metric else "Purples",
        title="Toronto Rental Market by Zone",
    )
