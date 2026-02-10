# Sprint 9-10 - Figure Factory Pattern for Reusable Charts

## Context
Creating multiple chart types across 5 dashboard tabs, with consistent styling and behavior needed across all visualizations.

## Problem
Without a standardized approach, each callback would create figures inline with:
- Duplicated styling code (colors, fonts, backgrounds)
- Inconsistent hover templates
- Hard-to-maintain figure creation logic
- No reuse between tabs

## Solution
Created a `figures/` module with factory functions:

```
figures/
├── __init__.py           # Exports all factories
├── choropleth.py         # Map visualizations
├── bar_charts.py         # ranking_bar, stacked_bar, horizontal_bar
├── scatter.py            # scatter_figure, bubble_chart
├── radar.py              # radar_figure, comparison_radar
└── demographics.py       # age_pyramid, donut_chart
```

Factory pattern benefits:
1. **Consistent styling** - dark theme applied once
2. **Type-safe interfaces** - clear parameters for each chart type
3. **Easy testing** - factories can be unit tested with sample data
4. **Reusability** - same factory used across multiple tabs

Example factory signature:
```python
def create_ranking_bar(
    data: list[dict],
    name_column: str,
    value_column: str,
    title: str = "",
    top_n: int = 5,
    bottom_n: int = 5,
    top_color: str = "#4CAF50",
    bottom_color: str = "#F44336",
) -> go.Figure:
```

## Prevention
- **Create factories early** - before implementing callbacks
- **Design generic interfaces** - factories should work with any data matching the schema
- **Apply styling in one place** - use constants for colors, fonts
- **Test factories independently** - with synthetic data before integration

## Tags
plotly, dash, design-patterns, python, visualization, reusability, code-organization
