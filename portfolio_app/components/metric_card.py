"""Metric card components for KPI display."""

from typing import Any

import dash_mantine_components as dmc
from dash import dcc

from portfolio_app.figures.toronto.summary_cards import create_metric_card_figure


class MetricCard:
    """A reusable metric card component."""

    def __init__(
        self,
        id_prefix: str,
        title: str,
        value: float | int | str = 0,
        delta: float | None = None,
        prefix: str = "",
        suffix: str = "",
        format_spec: str = ",.0f",
        positive_is_good: bool = True,
    ):
        """Initialize a metric card.

        Args:
            id_prefix: Prefix for component IDs.
            title: Card title.
            value: Main metric value.
            delta: Change value for delta indicator.
            prefix: Value prefix (e.g., '$').
            suffix: Value suffix.
            format_spec: Python format specification.
            positive_is_good: Whether positive delta is good.
        """
        self.id_prefix = id_prefix
        self.title = title
        self.value = value
        self.delta = delta
        self.prefix = prefix
        self.suffix = suffix
        self.format_spec = format_spec
        self.positive_is_good = positive_is_good

    def render(self) -> dmc.Paper:
        """Render the metric card component.

        Returns:
            Mantine Paper component with embedded graph.
        """
        fig = create_metric_card_figure(
            value=self.value,
            title=self.title,
            delta=self.delta,
            prefix=self.prefix,
            suffix=self.suffix,
            format_spec=self.format_spec,
            positive_is_good=self.positive_is_good,
        )

        return dmc.Paper(
            children=[
                dcc.Graph(
                    id=f"{self.id_prefix}-graph",
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "120px"},
                )
            ],
            p="xs",
            radius="sm",
            withBorder=True,
        )


def create_metric_cards_row(
    metrics: list[dict[str, Any]],
    id_prefix: str = "metric",
) -> dmc.SimpleGrid:
    """Create a row of metric cards.

    Args:
        metrics: List of metric configurations with keys:
            - title: Card title
            - value: Metric value
            - delta: Optional change value
            - prefix: Optional value prefix
            - suffix: Optional value suffix
            - format_spec: Optional format specification
            - positive_is_good: Optional delta color logic
        id_prefix: Prefix for component IDs.

    Returns:
        Mantine SimpleGrid component with metric cards.
    """
    cards = []
    for i, metric in enumerate(metrics):
        card = MetricCard(
            id_prefix=f"{id_prefix}-{i}",
            title=metric.get("title", ""),
            value=metric.get("value", 0),
            delta=metric.get("delta"),
            prefix=metric.get("prefix", ""),
            suffix=metric.get("suffix", ""),
            format_spec=metric.get("format_spec", ",.0f"),
            positive_is_good=metric.get("positive_is_good", True),
        )
        cards.append(card.render())

    return dmc.SimpleGrid(
        cols={"base": 1, "sm": 2, "md": len(cards)},
        spacing="md",
        children=cards,
    )
