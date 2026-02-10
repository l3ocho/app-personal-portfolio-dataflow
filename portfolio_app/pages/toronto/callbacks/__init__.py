"""Toronto dashboard callbacks.

Registers all callbacks for the neighbourhood dashboard including:
- Map interactions (choropleth click, metric selection)
- Chart updates (supporting visualizations)
- Selection handling (neighbourhood dropdown, details panels)
"""

# Import all callback modules to register them with Dash
from . import (
    chart_callbacks,  # noqa: F401
    map_callbacks,  # noqa: F401
    selection_callbacks,  # noqa: F401
)
