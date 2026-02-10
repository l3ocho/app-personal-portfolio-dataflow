"""Tab modules for Toronto Neighbourhood Dashboard."""

from .amenities import create_amenities_tab
from .demographics import create_demographics_tab
from .housing import create_housing_tab
from .overview import create_overview_tab
from .safety import create_safety_tab

__all__ = [
    "create_overview_tab",
    "create_housing_tab",
    "create_safety_tab",
    "create_demographics_tab",
    "create_amenities_tab",
]
