"""Bar chart figure factories for dashboard visualizations."""

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from portfolio_app.design import (
    CHART_PALETTE,
    COLOR_NEGATIVE,
    COLOR_POSITIVE,
    GRID_COLOR,
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_ranking_bar(
    data: list[dict[str, Any]],
    name_column: str,
    value_column: str,
    title: str | None = None,
    top_n: int = 10,
    bottom_n: int = 10,
    color_top: str = COLOR_POSITIVE,
    color_bottom: str = COLOR_NEGATIVE,
    value_format: str = ",.0f",
) -> go.Figure:
    """Create horizontal bar chart showing top and bottom rankings.

    Args:
        data: List of data records.
        name_column: Column name for labels.
        value_column: Column name for values.
        title: Optional chart title.
        top_n: Number of top items to show.
        bottom_n: Number of bottom items to show.
        color_top: Color for top performers.
        color_bottom: Color for bottom performers.
        value_format: Number format string for values.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Rankings")

    df = pd.DataFrame(data).sort_values(value_column, ascending=False)

    # Get top and bottom
    top_df = df.head(top_n).copy()
    bottom_df = df.tail(bottom_n).copy()

    top_df["group"] = "Top"
    bottom_df["group"] = "Bottom"

    # Combine with gap in the middle
    combined = pd.concat([top_df, bottom_df])
    combined["color"] = combined["group"].map(
        {"Top": color_top, "Bottom": color_bottom}
    )

    fig = go.Figure()

    # Add top bars
    fig.add_trace(
        go.Bar(
            y=top_df[name_column],
            x=top_df[value_column],
            orientation="h",
            marker_color=color_top,
            name="Top",
            text=top_df[value_column].apply(lambda x: f"{x:{value_format}}"),
            textposition="auto",
            hovertemplate=f"%{{y}}<br>{value_column}: %{{x:{value_format}}}<extra></extra>",
        )
    )

    # Add bottom bars
    fig.add_trace(
        go.Bar(
            y=bottom_df[name_column],
            x=bottom_df[value_column],
            orientation="h",
            marker_color=color_bottom,
            name="Bottom",
            text=bottom_df[value_column].apply(lambda x: f"{x:{value_format}}"),
            textposition="auto",
            hovertemplate=f"%{{y}}<br>{value_column}: %{{x:{value_format}}}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        barmode="group",
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "title": None},
        yaxis={"autorange": "reversed", "title": None},
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
    )

    return fig


def create_stacked_bar(
    data: list[dict[str, Any]],
    x_column: str,
    value_column: str,
    category_column: str,
    title: str | None = None,
    color_map: dict[str, str] | None = None,
    show_percentages: bool = False,
) -> go.Figure:
    """Create stacked bar chart for breakdown visualizations.

    Args:
        data: List of data records.
        x_column: Column name for x-axis categories.
        value_column: Column name for values.
        category_column: Column name for stacking categories.
        title: Optional chart title.
        color_map: Mapping of category to color.
        show_percentages: Whether to normalize to 100%.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Breakdown")

    df = pd.DataFrame(data)

    # Default color scheme using accessible palette
    if color_map is None:
        categories = df[category_column].unique()
        colors = CHART_PALETTE[: len(categories)]
        color_map = dict(zip(categories, colors, strict=False))

    fig = px.bar(
        df,
        x=x_column,
        y=value_column,
        color=category_column,
        color_discrete_map=color_map,
        barmode="stack",
        text=value_column if not show_percentages else None,
    )

    if show_percentages:
        fig.update_traces(texttemplate="%{y:.1f}%", textposition="inside")

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "title": None},
        yaxis={"gridcolor": GRID_COLOR, "title": None},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )

    return fig


def create_horizontal_bar(
    data: list[dict[str, Any]],
    name_column: str,
    value_column: str,
    title: str | None = None,
    color: str = CHART_PALETTE[0],
    value_format: str = ",.0f",
    sort: bool = True,
) -> go.Figure:
    """Create simple horizontal bar chart.

    Args:
        data: List of data records.
        name_column: Column name for labels.
        value_column: Column name for values.
        title: Optional chart title.
        color: Bar color.
        value_format: Number format string.
        sort: Whether to sort by value descending.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Bar Chart")

    df = pd.DataFrame(data)

    if sort:
        df = df.sort_values(value_column, ascending=True)

    fig = go.Figure(
        go.Bar(
            y=df[name_column],
            x=df[value_column],
            orientation="h",
            marker_color=color,
            text=df[value_column].apply(lambda x: f"{x:{value_format}}"),
            textposition="outside",
            hovertemplate=f"%{{y}}<br>Value: %{{x:{value_format}}}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "title": None},
        yaxis={"title": None},
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
