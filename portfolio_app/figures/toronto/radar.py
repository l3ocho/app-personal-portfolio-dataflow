"""Radar/spider chart figure factory for multi-metric comparison."""

from typing import Any

import plotly.graph_objects as go

from portfolio_app.design import (
    CHART_PALETTE,
    GRID_COLOR_DARK,
    PAPER_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_radar_figure(
    data: list[dict[str, Any]],
    metrics: list[str],
    name_column: str | None = None,
    title: str | None = None,
    fill: bool = True,
    colors: list[str] | None = None,
) -> go.Figure:
    """Create radar/spider chart for multi-axis comparison.

    Each record in data represents one entity (e.g., a neighbourhood)
    with values for each metric that will be plotted on a separate axis.

    Args:
        data: List of data records, each with values for the metrics.
        metrics: List of metric column names to display on radar axes.
        name_column: Column name for entity labels.
        title: Optional chart title.
        fill: Whether to fill the radar polygons.
        colors: List of colors for each data series.

    Returns:
        Plotly Figure object.
    """
    if not data or not metrics:
        return _create_empty_figure(title or "Radar Chart")

    # Use accessible palette by default
    if colors is None:
        colors = CHART_PALETTE

    fig = go.Figure()

    # Format axis labels
    axis_labels = [m.replace("_", " ").title() for m in metrics]

    for i, record in enumerate(data):
        values = [record.get(m, 0) or 0 for m in metrics]
        # Close the radar polygon
        values_closed = values + [values[0]]
        labels_closed = axis_labels + [axis_labels[0]]

        name = (
            record.get(name_column, f"Series {i + 1}")
            if name_column
            else f"Series {i + 1}"
        )
        color = colors[i % len(colors)]

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=labels_closed,
                name=name,
                line={"color": color, "width": 2},
                fill="toself" if fill else None,
                fillcolor=f"rgba{_hex_to_rgba(color, 0.2)}" if fill else None,
                hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=title,
        polar={
            "radialaxis": {
                "visible": True,
                "gridcolor": GRID_COLOR_DARK,
                "linecolor": GRID_COLOR_DARK,
                "tickfont": {"color": TEXT_PRIMARY},
            },
            "angularaxis": {
                "gridcolor": GRID_COLOR_DARK,
                "linecolor": GRID_COLOR_DARK,
                "tickfont": {"color": TEXT_PRIMARY},
            },
            "bgcolor": PAPER_BG,
        },
        paper_bgcolor=PAPER_BG,
        font_color=TEXT_PRIMARY,
        showlegend=len(data) > 1,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.2},
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
    )

    return fig


def create_comparison_radar(
    selected_data: dict[str, Any],
    average_data: dict[str, Any],
    metrics: list[str],
    selected_name: str = "Selected",
    average_name: str = "City Average",
    title: str | None = None,
) -> go.Figure:
    """Create radar chart comparing a selection to city average.

    Args:
        selected_data: Data for the selected entity.
        average_data: Data for the city average.
        metrics: List of metric column names.
        selected_name: Label for selected entity.
        average_name: Label for average.
        title: Optional chart title.

    Returns:
        Plotly Figure object.
    """
    if not selected_data or not average_data:
        return _create_empty_figure(title or "Comparison")

    data = [
        {**selected_data, "__name__": selected_name},
        {**average_data, "__name__": average_name},
    ]

    return create_radar_figure(
        data=data,
        metrics=metrics,
        name_column="__name__",
        title=title,
        colors=[CHART_PALETTE[3], TEXT_SECONDARY],  # Teal for selected, gray for avg
    )


def _hex_to_rgba(hex_color: str, alpha: float) -> tuple[int, int, int, float]:
    """Convert hex color to RGBA tuple."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


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
        font_color=TEXT_PRIMARY,
    )
    return fig
