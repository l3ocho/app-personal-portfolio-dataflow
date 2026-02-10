"""Demographics-specific chart factories."""

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from portfolio_app.design import (
    CHART_PALETTE,
    GRID_COLOR,
    PALETTE_GENDER,
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_age_pyramid(
    data: list[dict[str, Any]],
    age_groups: list[str],
    male_column: str = "male",
    female_column: str = "female",
    title: str | None = None,
) -> go.Figure:
    """Create population pyramid by age and gender.

    Args:
        data: List with one record per age group containing male/female counts.
        age_groups: List of age group labels in order (youngest to oldest).
        male_column: Column name for male population.
        female_column: Column name for female population.
        title: Optional chart title.

    Returns:
        Plotly Figure object.
    """
    if not data or not age_groups:
        return _create_empty_figure(title or "Age Distribution")

    df = pd.DataFrame(data)

    # Ensure data is ordered by age groups
    if "age_group" in df.columns:
        df["age_order"] = df["age_group"].apply(
            lambda x: age_groups.index(x) if x in age_groups else -1
        )
        df = df.sort_values("age_order")

    male_values = df[male_column].tolist() if male_column in df.columns else []
    female_values = df[female_column].tolist() if female_column in df.columns else []

    # Make male values negative for pyramid effect
    male_values_neg = [-v for v in male_values]

    fig = go.Figure()

    # Male bars (left side, negative values)
    fig.add_trace(
        go.Bar(
            y=age_groups,
            x=male_values_neg,
            orientation="h",
            name="Male",
            marker_color=PALETTE_GENDER["male"],
            hovertemplate="%{y}<br>Male: %{customdata:,}<extra></extra>",
            customdata=male_values,
        )
    )

    # Female bars (right side, positive values)
    fig.add_trace(
        go.Bar(
            y=age_groups,
            x=female_values,
            orientation="h",
            name="Female",
            marker_color=PALETTE_GENDER["female"],
            hovertemplate="%{y}<br>Female: %{x:,}<extra></extra>",
        )
    )

    # Calculate max for symmetric axis
    max_val = max(max(male_values, default=0), max(female_values, default=0))

    fig.update_layout(
        title=title,
        barmode="overlay",
        bargap=0.1,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={
            "title": "Population",
            "gridcolor": GRID_COLOR,
            "range": [-max_val * 1.1, max_val * 1.1],
            "tickvals": [-max_val, -max_val / 2, 0, max_val / 2, max_val],
            "ticktext": [
                f"{max_val:,.0f}",
                f"{max_val / 2:,.0f}",
                "0",
                f"{max_val / 2:,.0f}",
                f"{max_val:,.0f}",
            ],
        },
        yaxis={"title": None, "gridcolor": GRID_COLOR},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )

    return fig


def create_donut_chart(
    data: list[dict[str, Any]],
    name_column: str,
    value_column: str,
    title: str | None = None,
    colors: list[str] | None = None,
    hole_size: float = 0.4,
) -> go.Figure:
    """Create donut chart for percentage breakdowns.

    Args:
        data: List of data records with name and value.
        name_column: Column name for labels.
        value_column: Column name for values.
        title: Optional chart title.
        colors: List of colors for segments.
        hole_size: Size of center hole (0-1).

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Distribution")

    df = pd.DataFrame(data)

    # Use accessible palette by default
    if colors is None:
        colors = CHART_PALETTE

    fig = go.Figure(
        go.Pie(
            labels=df[name_column],
            values=df[value_column],
            hole=hole_size,
            marker_colors=colors[: len(df)],
            textinfo="percent+label",
            textposition="outside",
            hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        font_color=TEXT_PRIMARY,
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )

    return fig


def create_income_distribution(
    data: list[dict[str, Any]],
    bracket_column: str,
    count_column: str,
    title: str | None = None,
    color: str = CHART_PALETTE[3],  # Teal
) -> go.Figure:
    """Create histogram-style bar chart for income distribution.

    Args:
        data: List of data records with income brackets and counts.
        bracket_column: Column name for income brackets.
        count_column: Column name for household counts.
        title: Optional chart title.
        color: Bar color.

    Returns:
        Plotly Figure object.
    """
    if not data:
        return _create_empty_figure(title or "Income Distribution")

    df = pd.DataFrame(data)

    fig = go.Figure(
        go.Bar(
            x=df[bracket_column],
            y=df[count_column],
            marker_color=color,
            text=df[count_column].apply(lambda x: f"{x:,}"),
            textposition="outside",
            hovertemplate="%{x}<br>Households: %{y:,}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font_color=TEXT_PRIMARY,
        xaxis={
            "title": "Income Bracket",
            "gridcolor": GRID_COLOR,
            "tickangle": -45,
        },
        yaxis={
            "title": "Households",
            "gridcolor": GRID_COLOR,
        },
        margin={"l": 10, "r": 10, "t": 60, "b": 80},
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
