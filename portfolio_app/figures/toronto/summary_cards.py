"""Summary card figure factories for KPI display."""

from typing import Any

import plotly.graph_objects as go

from portfolio_app.design import (
    COLOR_NEGATIVE,
    COLOR_POSITIVE,
    PAPER_BG,
    PLOT_BG,
    TEXT_PRIMARY,
)


def create_metric_card_figure(
    value: float | int | str,
    title: str,
    delta: float | None = None,
    delta_suffix: str = "%",
    prefix: str = "",
    suffix: str = "",
    format_spec: str = ",.0f",
    positive_is_good: bool = True,
) -> go.Figure:
    """Create a KPI indicator figure.

    Args:
        value: The main metric value.
        title: Card title.
        delta: Optional change value (for delta indicator).
        delta_suffix: Suffix for delta value (e.g., '%').
        prefix: Prefix for main value (e.g., '$').
        suffix: Suffix for main value.
        format_spec: Python format specification for the value.
        positive_is_good: Whether positive delta is good (green) or bad (red).

    Returns:
        Plotly Figure object.
    """
    # Determine numeric value for indicator
    if isinstance(value, int | float):
        number_value: float | None = float(value)
    else:
        number_value = None

    fig = go.Figure()

    # Add indicator trace
    indicator_config: dict[str, Any] = {
        "mode": "number",
        "value": number_value if number_value is not None else 0,
        "title": {"text": title, "font": {"size": 14}},
        "number": {
            "font": {"size": 32},
            "prefix": prefix,
            "suffix": suffix,
            "valueformat": format_spec,
        },
    }

    # Add delta if provided
    if delta is not None:
        indicator_config["mode"] = "number+delta"
        indicator_config["delta"] = {
            "reference": number_value - delta if number_value else 0,
            "relative": False,
            "valueformat": ".1f",
            "suffix": delta_suffix,
            "increasing": {
                "color": COLOR_POSITIVE if positive_is_good else COLOR_NEGATIVE
            },
            "decreasing": {
                "color": COLOR_NEGATIVE if positive_is_good else COLOR_POSITIVE
            },
        }

    fig.add_trace(go.Indicator(**indicator_config))

    fig.update_layout(
        height=120,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font={"family": "Inter, sans-serif", "color": TEXT_PRIMARY},
    )

    return fig


def create_summary_metrics(
    metrics: dict[str, dict[str, Any]],
) -> list[go.Figure]:
    """Create multiple metric card figures.

    Args:
        metrics: Dictionary of metric configurations.
            Key: metric name
            Value: dict with 'value', 'title', 'delta' (optional), etc.

    Returns:
        List of Plotly Figure objects.
    """
    figures = []

    for metric_config in metrics.values():
        fig = create_metric_card_figure(
            value=metric_config.get("value", 0),
            title=metric_config.get("title", ""),
            delta=metric_config.get("delta"),
            delta_suffix=metric_config.get("delta_suffix", "%"),
            prefix=metric_config.get("prefix", ""),
            suffix=metric_config.get("suffix", ""),
            format_spec=metric_config.get("format_spec", ",.0f"),
            positive_is_good=metric_config.get("positive_is_good", True),
        )
        figures.append(fig)

    return figures
