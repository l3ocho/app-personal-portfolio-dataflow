"""Time series figure factories for Toronto housing data."""

from typing import Any

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


def create_price_time_series(
    data: list[dict[str, Any]],
    date_column: str = "full_date",
    price_column: str = "avg_price",
    group_column: str | None = None,
    title: str = "Average Price Over Time",
    show_yoy: bool = True,
) -> go.Figure:
    """Create a time series chart for price data.

    Args:
        data: List of records with date and price columns.
        date_column: Column name for dates.
        price_column: Column name for price values.
        group_column: Optional column for grouping (e.g., district_code).
        title: Chart title.
        show_yoy: Whether to show year-over-year change annotations.

    Returns:
        Plotly Figure object.
    """
    import pandas as pd

    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"color": TEXT_SECONDARY},
        )
        fig.update_layout(
            title=title,
            height=350,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            font_color=TEXT_PRIMARY,
        )
        return fig

    df = pd.DataFrame(data)
    df[date_column] = pd.to_datetime(df[date_column])

    if group_column and group_column in df.columns:
        fig = px.line(
            df,
            x=date_column,
            y=price_column,
            color=group_column,
            title=title,
            color_discrete_sequence=CHART_PALETTE,
        )
    else:
        fig = px.line(
            df,
            x=date_column,
            y=price_column,
            title=title,
        )
        fig.update_traces(line_color=CHART_PALETTE[0])

    fig.update_layout(
        height=350,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        xaxis_title="Date",
        yaxis_title=price_column.replace("_", " ").title(),
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
        yaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
    )

    return fig


def create_volume_time_series(
    data: list[dict[str, Any]],
    date_column: str = "full_date",
    volume_column: str = "sales_count",
    group_column: str | None = None,
    title: str = "Sales Volume Over Time",
    chart_type: str = "bar",
) -> go.Figure:
    """Create a time series chart for volume/count data.

    Args:
        data: List of records with date and volume columns.
        date_column: Column name for dates.
        volume_column: Column name for volume values.
        group_column: Optional column for grouping.
        title: Chart title.
        chart_type: 'bar' or 'line'.

    Returns:
        Plotly Figure object.
    """
    import pandas as pd

    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"color": TEXT_SECONDARY},
        )
        fig.update_layout(
            title=title,
            height=350,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            font_color=TEXT_PRIMARY,
        )
        return fig

    df = pd.DataFrame(data)
    df[date_column] = pd.to_datetime(df[date_column])

    if chart_type == "bar":
        if group_column and group_column in df.columns:
            fig = px.bar(
                df,
                x=date_column,
                y=volume_column,
                color=group_column,
                title=title,
                color_discrete_sequence=CHART_PALETTE,
            )
        else:
            fig = px.bar(
                df,
                x=date_column,
                y=volume_column,
                title=title,
            )
            fig.update_traces(marker_color=CHART_PALETTE[0])
    else:
        if group_column and group_column in df.columns:
            fig = px.line(
                df,
                x=date_column,
                y=volume_column,
                color=group_column,
                title=title,
                color_discrete_sequence=CHART_PALETTE,
            )
        else:
            fig = px.line(
                df,
                x=date_column,
                y=volume_column,
                title=title,
            )
            fig.update_traces(line_color=CHART_PALETTE[0])

    fig.update_layout(
        height=350,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        xaxis_title="Date",
        yaxis_title=volume_column.replace("_", " ").title(),
        yaxis_tickformat=",",
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
        yaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
    )

    return fig


def create_market_comparison_chart(
    data: list[dict[str, Any]],
    date_column: str = "full_date",
    metrics: list[str] | None = None,
    title: str = "Market Indicators",
) -> go.Figure:
    """Create a multi-metric comparison chart.

    Args:
        data: List of records with date and metric columns.
        date_column: Column name for dates.
        metrics: List of metric columns to display.
        title: Chart title.

    Returns:
        Plotly Figure object with secondary y-axis.
    """
    import pandas as pd
    from plotly.subplots import make_subplots

    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"color": TEXT_SECONDARY},
        )
        fig.update_layout(
            title=title,
            height=400,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PLOT_BG,
            font_color=TEXT_PRIMARY,
        )
        return fig

    if metrics is None:
        metrics = ["avg_price", "sales_count"]

    df = pd.DataFrame(data)
    df[date_column] = pd.to_datetime(df[date_column])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for i, metric in enumerate(metrics[:4]):
        if metric not in df.columns:
            continue

        secondary = i > 0
        fig.add_trace(
            go.Scatter(
                x=df[date_column],
                y=df[metric],
                name=metric.replace("_", " ").title(),
                line={"color": CHART_PALETTE[i % len(CHART_PALETTE)]},
            ),
            secondary_y=secondary,
        )

    fig.update_layout(
        title=title,
        height=400,
        margin={"l": 40, "r": 40, "t": 50, "b": 40},
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
        yaxis={"gridcolor": GRID_COLOR, "linecolor": GRID_COLOR},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": TEXT_PRIMARY},
        },
    )

    return fig


def add_policy_markers(
    fig: go.Figure,
    policy_events: list[dict[str, Any]],
    date_column: str = "event_date",
    y_position: float | None = None,
) -> go.Figure:
    """Add policy event markers to an existing time series figure.

    Args:
        fig: Existing Plotly figure to add markers to.
        policy_events: List of policy event dicts with date and metadata.
        date_column: Column name for event dates.
        y_position: Y position for markers. If None, uses top of chart.

    Returns:
        Updated Plotly Figure object with policy markers.
    """
    if not policy_events:
        return fig

    # Color mapping for policy categories using design tokens
    category_colors = {
        "monetary": CHART_PALETTE[0],  # Blue
        "tax": CHART_PALETTE[3],  # Teal/green
        "regulatory": CHART_PALETTE[1],  # Orange
        "supply": CHART_PALETTE[6],  # Pink
        "economic": CHART_PALETTE[5],  # Vermillion
    }

    # Symbol mapping for expected direction
    direction_symbols = {
        "bullish": "triangle-up",
        "bearish": "triangle-down",
        "neutral": "circle",
    }

    for event in policy_events:
        event_date = event.get(date_column)
        category = event.get("category", "economic")
        direction = event.get("expected_direction", "neutral")
        title = event.get("title", "Policy Event")
        level = event.get("level", "federal")

        color = category_colors.get(category, TEXT_SECONDARY)
        symbol = direction_symbols.get(direction, "circle")

        # Add vertical line for the event
        fig.add_vline(
            x=event_date,
            line_dash="dot",
            line_color=color,
            opacity=0.5,
            annotation_text="",
        )

        # Add marker with hover info
        fig.add_trace(
            go.Scatter(
                x=[event_date],
                y=[y_position] if y_position else [None],  # type: ignore[list-item]
                mode="markers",
                marker={
                    "symbol": symbol,
                    "size": 12,
                    "color": color,
                    "line": {"width": 1, "color": TEXT_PRIMARY},
                },
                name=title,
                hovertemplate=(
                    f"<b>{title}</b><br>"
                    f"Date: %{{x}}<br>"
                    f"Level: {level.title()}<br>"
                    f"Category: {category.title()}<br>"
                    f"<extra></extra>"
                ),
                showlegend=False,
            )
        )

    return fig


def create_time_series_with_events(
    data: list[dict[str, Any]],
    policy_events: list[dict[str, Any]],
    date_column: str = "full_date",
    value_column: str = "avg_price",
    title: str = "Price Trend with Policy Events",
) -> go.Figure:
    """Create a time series chart with policy event markers.

    Args:
        data: Time series data.
        policy_events: Policy events to overlay.
        date_column: Column name for dates.
        value_column: Column name for values.
        title: Chart title.

    Returns:
        Plotly Figure with time series and policy markers.
    """
    # Create base time series
    fig = create_price_time_series(
        data=data,
        date_column=date_column,
        price_column=value_column,
        title=title,
    )

    # Add policy markers at the top of the chart
    if policy_events:
        fig = add_policy_markers(fig, policy_events)

    return fig
