"""Centralized design tokens for consistent styling across the application.

This module provides a single source of truth for colors, ensuring:
- Consistent styling across all Plotly figures and components
- Accessibility compliance (WCAG color contrast)
- Easy theme updates without hunting through multiple files

Usage:
    from portfolio_app.design import TEXT_PRIMARY, CHART_PALETTE
    fig.update_layout(font_color=TEXT_PRIMARY)
"""

from typing import Any

# =============================================================================
# TEXT COLORS (Dark Theme)
# =============================================================================

TEXT_PRIMARY = "#c9c9c9"
"""Primary text color for labels, titles, and body text."""

TEXT_SECONDARY = "#888888"
"""Secondary text color for subtitles, captions, and muted text."""

TEXT_MUTED = "#666666"
"""Muted text color for disabled states and placeholders."""


# =============================================================================
# CHART BACKGROUND & GRID
# =============================================================================

GRID_COLOR = "rgba(128, 128, 128, 0.2)"
"""Standard grid line color with transparency."""

GRID_COLOR_DARK = "rgba(128, 128, 128, 0.3)"
"""Darker grid for radar charts and polar plots."""

PAPER_BG = "rgba(0, 0, 0, 0)"
"""Transparent paper background for charts."""

PLOT_BG = "rgba(0, 0, 0, 0)"
"""Transparent plot background for charts."""


# =============================================================================
# SEMANTIC COLORS
# =============================================================================

COLOR_POSITIVE = "#40c057"
"""Positive/success indicator (Mantine green-6)."""

COLOR_NEGATIVE = "#fa5252"
"""Negative/error indicator (Mantine red-6)."""

COLOR_WARNING = "#fab005"
"""Warning indicator (Mantine yellow-6)."""

COLOR_ACCENT = "#228be6"
"""Primary accent color (Mantine blue-6)."""


# =============================================================================
# ACCESSIBLE CHART PALETTE
# =============================================================================

# Okabe-Ito palette - optimized for all color vision deficiencies
# Reference: https://jfly.uni-koeln.de/color/
CHART_PALETTE = [
    "#0072B2",  # Blue (primary data series)
    "#E69F00",  # Orange
    "#56B4E9",  # Sky blue
    "#009E73",  # Teal/green
    "#F0E442",  # Yellow
    "#D55E00",  # Vermillion
    "#CC79A7",  # Pink
    "#000000",  # Black (use sparingly)
]
"""
Accessible categorical palette (Okabe-Ito).

Distinguishable for deuteranopia, protanopia, and tritanopia.
Use indices 0-6 for most charts; index 7 (black) for emphasis only.
"""

# Semantic subsets for specific use cases
PALETTE_COMPARISON = [CHART_PALETTE[0], CHART_PALETTE[1]]
"""Two-color palette for A/B comparisons."""

PALETTE_GENDER = {
    "male": "#56B4E9",  # Sky blue
    "female": "#CC79A7",  # Pink
}
"""Gender-specific colors (accessible contrast)."""

PALETTE_TREND = {
    "positive": COLOR_POSITIVE,
    "negative": COLOR_NEGATIVE,
    "neutral": TEXT_SECONDARY,
}
"""Trend indicator colors for sparklines and deltas."""


# =============================================================================
# POLICY/EVENT MARKERS (Time Series)
# =============================================================================

POLICY_COLORS = {
    "policy_change": "#E69F00",  # Orange - policy changes
    "major_event": "#D55E00",  # Vermillion - major events
    "data_note": "#56B4E9",  # Sky blue - data annotations
    "forecast": "#009E73",  # Teal - forecast periods
    "highlight": "#F0E442",  # Yellow - highlighted regions
}
"""Colors for policy markers and event annotations on time series."""


# =============================================================================
# CHART LAYOUT DEFAULTS
# =============================================================================


def get_default_layout() -> dict[str, Any]:
    """Return default Plotly layout settings with design tokens.

    Returns:
        dict: Layout configuration for fig.update_layout()

    Example:
        fig.update_layout(**get_default_layout())
    """
    return {
        "paper_bgcolor": PAPER_BG,
        "plot_bgcolor": PLOT_BG,
        "font": {"color": TEXT_PRIMARY},
        "title": {"font": {"color": TEXT_PRIMARY}},
        "legend": {"font": {"color": TEXT_PRIMARY}},
        "xaxis": {
            "gridcolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "tickfont": {"color": TEXT_PRIMARY},
            "title": {"font": {"color": TEXT_PRIMARY}},
        },
        "yaxis": {
            "gridcolor": GRID_COLOR,
            "linecolor": GRID_COLOR,
            "tickfont": {"color": TEXT_PRIMARY},
            "title": {"font": {"color": TEXT_PRIMARY}},
        },
    }


def get_colorbar_defaults() -> dict[str, Any]:
    """Return default colorbar settings with design tokens.

    Returns:
        dict: Colorbar configuration for choropleth/heatmap traces
    """
    return {
        "tickfont": {"color": TEXT_PRIMARY},
        "title": {"font": {"color": TEXT_PRIMARY}},
    }
