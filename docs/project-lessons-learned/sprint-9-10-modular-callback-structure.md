# Sprint 9-10 - Modular Callback Structure for Multi-Tab Dashboards

## Context
Implementing a 5-tab Toronto Neighbourhood Dashboard with multiple callbacks per tab (map updates, chart updates, KPI updates, selection handling).

## Problem
Initial callback implementation approach would have placed all callbacks in a single file, leading to:
- A monolithic file with 500+ lines
- Difficult-to-navigate code
- Callbacks for different tabs interleaved
- Testing difficulties

## Solution
Organized callbacks into three focused modules:

```
callbacks/
├── __init__.py              # Imports all modules to register callbacks
├── map_callbacks.py         # Choropleth updates, map click handling
├── chart_callbacks.py       # Supporting chart updates (scatter, trend, donut)
└── selection_callbacks.py   # Dropdown population, KPI updates
```

Key patterns:
1. **Group by responsibility**, not by tab - all map-related callbacks together
2. **Use noqa comments** for imports that register callbacks as side effects
3. **Share helper functions** (like `_empty_chart()`) within modules

```python
# callbacks/__init__.py
from . import (
    chart_callbacks,  # noqa: F401
    map_callbacks,  # noqa: F401
    selection_callbacks,  # noqa: F401
)
```

## Prevention
- **Plan callback organization before implementation** - sketch which callbacks go where
- **Group by function, not by feature** - keeps related logic together
- **Keep modules under 400 lines** - split if exceeding
- **Test imports early** - verify callbacks register correctly

## Tags
dash, callbacks, architecture, python, code-organization, maintainability
