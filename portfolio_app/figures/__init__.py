"""Plotly figure factories for data visualization.

Figure factories are organized by dashboard domain:
- toronto/  : Toronto Neighbourhood Dashboard figures

Usage:
    from portfolio_app.figures.toronto import create_choropleth_figure
    from portfolio_app.figures.toronto import create_ranking_bar
"""

from . import toronto

__all__ = [
    "toronto",
]
