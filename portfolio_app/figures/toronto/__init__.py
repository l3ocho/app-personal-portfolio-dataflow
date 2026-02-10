"""Plotly figure factories for Toronto dashboard visualizations."""

from .bar_charts import (
    create_horizontal_bar,
    create_ranking_bar,
    create_stacked_bar,
)
from .choropleth import (
    create_choropleth_figure,
    create_zone_map,
)
from .demographics import (
    create_age_pyramid,
    create_donut_chart,
    create_income_distribution,
)
from .radar import (
    create_comparison_radar,
    create_radar_figure,
)
from .scatter import (
    create_bubble_chart,
    create_scatter_figure,
)
from .summary_cards import create_metric_card_figure, create_summary_metrics
from .time_series import (
    add_policy_markers,
    create_market_comparison_chart,
    create_price_time_series,
    create_time_series_with_events,
    create_volume_time_series,
)

__all__ = [
    # Choropleth
    "create_choropleth_figure",
    "create_zone_map",
    # Time series
    "create_price_time_series",
    "create_volume_time_series",
    "create_market_comparison_chart",
    "create_time_series_with_events",
    "add_policy_markers",
    # Summary
    "create_metric_card_figure",
    "create_summary_metrics",
    # Bar charts
    "create_ranking_bar",
    "create_stacked_bar",
    "create_horizontal_bar",
    # Scatter plots
    "create_scatter_figure",
    "create_bubble_chart",
    # Radar charts
    "create_radar_figure",
    "create_comparison_radar",
    # Demographics
    "create_age_pyramid",
    "create_donut_chart",
    "create_income_distribution",
]
