"""Scatter plot figure factory for correlation views."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from portfolio_app.design import (
    CHART_PALETTE,
    GRID_COLOR,
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_scatter_figure(
    data: list[dict[str, Any]],
    x_column: str,
    y_column: str,
    name_column: str | None = None,
    size_column: str | None = None,
    color_column: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    trendline: bool = False,
    color_scale: str = "Blues",
) -> go.Figure:
    """Create scatter plot for correlation visualization.

    Args:
        data: List of data records.
        x_column: Column name for x-axis values.
        y_column: Column name for y-axis values.
        name_column: Column name for point labels (hover).
        size_column: Column name for point sizes.
        color_column: Column name for color encoding.
        title: Optional chart title.
        x_title: X-axis title.
        y_title: Y-axis title.
        trendline: Whether to add OLS trendline.
        color_scale: Plotly color scale for continuous colors.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Scatter Plot")

    df = pd.DataFrame(data)

    # Build hover_data
    hover_data = {}
    if name_column and name_column in df.columns:
        hover_data[name_column] = True

    # Create scatter plot
    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        size=size_column if size_column and size_column in df.columns else None,
        color=color_column if color_column and color_column in df.columns else None,
        color_continuous_scale=color_scale,
        hover_name=name_column,
        trendline="ols" if trendline else None,
        opacity=0.7,
    )

    # Style the markers
    fig.update_traces(
        marker={
            "line": {"width": 1, "color": "rgba(255,255,255,0.3)"},
        },
    )

    # Trendline styling
    if trendline:
        fig.update_traces(
            selector={"mode": "lines"},
            line={"color": CHART_PALETTE[1], "dash": "dash", "width": 2},
        )

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={
            "gridcolor": GRID_COLOR,
            "title": x_title or x_column.replace("_", " ").title(),
            "zeroline": False,
        },
        yaxis={
            "gridcolor": GRID_COLOR,
            "title": y_title or y_column.replace("_", " ").title(),
            "zeroline": False,
        },
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        showlegend=color_column is not None,
    )

    return fig


def create_bubble_chart(
    data: list[dict[str, Any]],
    x_column: str,
    y_column: str,
    size_column: str,
    name_column: str | None = None,
    color_column: str | None = None,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    size_max: int = 50,
) -> go.Figure:
    """Create bubble chart with sized markers.

    Args:
        data: List of data records.
        x_column: Column name for x-axis values.
        y_column: Column name for y-axis values.
        size_column: Column name for bubble sizes.
        name_column: Column name for labels.
        color_column: Column name for colors.
        title: Optional chart title.
        x_title: X-axis title.
        y_title: Y-axis title.
        size_max: Maximum marker size in pixels.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Bubble Chart")

    df = pd.DataFrame(data)

    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        size=size_column,
        color=color_column,
        hover_name=name_column,
        size_max=size_max,
        opacity=0.7,
        color_discrete_sequence=CHART_PALETTE,
    )

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={
            "gridcolor": GRID_COLOR,
            "title": x_title or x_column.replace("_", " ").title(),
        },
        yaxis={
            "gridcolor": GRID_COLOR,
            "title": y_title or y_column.replace("_", " ").title(),
        },
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
    )

    return fig


def _create_empty_figure(title: str) -> go.Figure:
    """Create an empty figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": TEXT_SECONDARY},
    )
    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig
